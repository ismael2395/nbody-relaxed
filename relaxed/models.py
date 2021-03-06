from abc import abstractmethod, ABC
from typing import Iterable
import numpy as np
from sklearn import linear_model
from sklearn.preprocessing import QuantileTransformer
from sklearn.feature_selection import SelectFromModel
from scipy.interpolate import interp1d

from relaxed.analysis import get_an_from_am


class PredictionModel(ABC):
    def __init__(self, n_features: int) -> None:
        assert isinstance(n_features, int) and n_features > 0
        self.n_features = n_features
        self.trained = False  # whether model has been trained yet.

    def predict(self, x):
        assert len(x.shape) == 2
        assert x.shape[1] == self.n_features
        assert np.sum(np.isnan(x)) == 0
        assert self.trained
        return self._predict(x)

    def fit(self, x, y):
        assert np.sum(np.isnan(x)) == np.sum(np.isnan(y)) == 0
        assert x.shape[0] == y.shape[0]
        assert len(y.shape) == 1 or y.shape[1] == 1
        assert len(x.shape) == 2
        assert x.shape[1] == self.n_features
        self._fit(x, y)
        self.trained = True

    @abstractmethod
    def _fit(self, x, y):
        pass

    @abstractmethod
    def _predict(self, x):
        pass


class PredictionModelTransform(PredictionModel, ABC):
    """Enable possibility of transforming variables before fitting/prediction."""

    def __init__(self, n_features: int, use_qt: bool = False, use_logs: bool = False) -> None:
        super().__init__(n_features)
        assert (use_logs + use_qt) <= 1

        self.use_qt = use_qt  # whether to transform data to be gaussian using quantiles.
        self.use_logs = use_logs  # whether to convert quantities to log space.

        # fit attributes
        self.qt_x = None
        self.qt_y = None

    def fit(self, x, y):

        if self.use_qt:
            self.qt_y = QuantileTransformer(n_quantiles=len(y), output_distribution="normal").fit(
                y.reshape(-1, 1)
            )
            self.qt_x = QuantileTransformer(n_quantiles=len(x), output_distribution="normal").fit(x)

            x_trans = self.qt_x.transform(x)
            y_trans = self.qt_y.transform(y.reshape(-1, 1)).reshape(-1)

            super().fit(x_trans, y_trans)

        elif self.use_logs:
            super().fit(np.log(x), np.log(y))

        else:
            super().fit(x, y)

    def predict(self, x):
        if self.use_qt:
            x_trans = self.qt_x.transform(x)
            y_trans = super().predict(x_trans)
            return self.qt_y.inverse_transform(y_trans.reshape(-1, 1)).reshape(-1)

        elif self.use_logs:
            return np.exp(super().predict(np.log(x)))
        else:
            return super().predict(x)


class LogNormalRandomSample(PredictionModel):
    """"Lognormal random samples."""

    def __init__(self, n_features: int) -> None:
        super().__init__(n_features)

        self.mu = None
        self.sigma = None

    def _fit(self, x, y):
        assert np.all(y > 0)
        mu, sigma = np.mean(np.log(y)), np.std(np.log(y))
        self.mu = mu
        self.sigma = sigma

    def _predict(self, x):
        n_test = len(x)
        return np.exp(np.random.normal(self.mu, self.sigma, n_test))


class LinearRegression(PredictionModelTransform):
    def __init__(self, n_features: int, use_qt: bool = False, use_logs: bool = False) -> None:
        super().__init__(n_features, use_qt, use_logs)
        self.reg = None

    def _fit(self, x, y):
        self.reg = linear_model.LinearRegression().fit(x, y)

    def _predict(self, x):
        return self.reg.predict(x)


class LASSO(PredictionModelTransform):
    name = "lasso"

    def __init__(self, n_features: int, alpha: float = 0.1, use_qt=False, use_logs=False) -> None:
        # alpha is the regularization parameter.
        super().__init__(n_features, use_qt, use_logs)
        self.alpha = alpha

        # attributes of fit
        self.lasso = None
        self.importance = None

    def _fit(self, x, y):
        # use lasso linear regression.
        _lasso = linear_model.Lasso(alpha=self.alpha)
        selector = SelectFromModel(estimator=_lasso).fit(x, y)
        self.lasso = _lasso.fit(x, y)
        self.importance = selector.estimator.coef_

    def _predict(self, x):
        return self.lasso.predict(x)


class MultiVariateGaussian(PredictionModelTransform):
    """Multi-Variate Gaussian using full covariance matrix (returns conditional mean)."""

    def __init__(self, n_features: int, use_qt: bool = False, use_logs: bool = False) -> None:
        super().__init__(n_features, use_qt, use_logs)

        self.mu1 = None
        self.mu2 = None
        self.Sigma = None
        self.rho = None
        self.sigma_cond = None

    def _fit(self, x, y):
        """
        We assume a multivariate-gaussian distribution P(X, a(m1), a(m2), ...) with
        conditional distribution P(X | {a(m_i)}) uses the rule here:
        https://stats.stackexchange.com/questions/30588/deriving-the-conditional-distributions-of-a-multivariate-normal-distribution
        we return the mean/std deviation of the conditional gaussian.

        * y (usually) represents one of the dark matter halo properties at z=0.
        * x are the features used for prediction, should have shape (y.shape[0], n_features)
        """
        n_features = self.n_features

        # calculate sigma/correlation matrix bewteen all quantities
        z = np.vstack([y.reshape(1, -1), x.T]).T

        # some sanity checks
        assert z.shape == (y.shape[0], n_features + 1)
        np.testing.assert_equal(y, z[:, 0])
        np.testing.assert_equal(x[:, 0], z[:, 1])  # ignore mutual nan's
        np.testing.assert_equal(x[:, -1], z[:, -1])

        # calculate covariances
        Sigma = np.zeros((1 + n_features, 1 + n_features))
        rho = np.zeros((1 + n_features, 1 + n_features))
        for i in range(n_features + 1):
            for j in range(n_features + 1):
                if i <= j:
                    # calculate correlation coefficient keeping only non-nan values
                    z1, z2 = z[:, i], z[:, j]
                    keep = ~np.isnan(z1) & ~np.isnan(z2)
                    cov = np.cov(z1[keep], z2[keep])
                    assert cov.shape == (2, 2)
                    Sigma[i, j] = cov[0, 1]
                    rho[i, j] = np.corrcoef(z1[keep], z2[keep])[0, 1]
                else:
                    rho[i, j] = rho[j, i]
                    Sigma[i, j] = Sigma[j, i]

        # more sanity
        assert np.all(~np.isnan(Sigma))
        assert np.all(~np.isnan(rho))

        mu1 = np.nanmean(y).reshape(1, 1)
        mu2 = np.nanmean(x, axis=0).reshape(n_features, 1)
        Sigma11 = Sigma[0, 0].reshape(1, 1)
        Sigma12 = Sigma[0, 1:].reshape(1, n_features)
        Sigma22 = Sigma[1:, 1:].reshape(n_features, n_features)
        sigma_cond = Sigma11 - Sigma12.dot(np.linalg.inv(Sigma22)).dot(Sigma12.T)

        # update prediction attributes
        self.mu1 = mu1
        self.mu2 = mu2
        self.Sigma = Sigma
        self.rho = rho
        self.sigma_cond = sigma_cond

    def _predict(self, x):
        # returns mu_cond evaluated given x.
        assert np.sum(np.isnan(x)) == 0
        x = x.reshape(-1, self.n_features).T
        mu_cond = self.mu1 + self.Sigma12.dot(np.linalg.inv(self.Sigma22)).dot(x - self.mu2)
        return mu_cond.reshape(-1)


class CAM(PredictionModel):
    """Conditional Abundance Matching"""

    def __init__(
        self, n_features: int, mass_bins: np.ndarray, mrange: Iterable, cam_order: int = -1
    ) -> None:
        # cam_order: +1 or -1 depending on correlation of a_{n} with y
        assert n_features == len(mass_bins)
        super().__init__(n_features)

        assert cam_order in {-1, 1}
        assert isinstance(mrange, Iterable) and len(mrange) == 2
        assert isinstance(mass_bins, np.ndarray)
        self.mrange = mrange
        self.cam_order = cam_order
        self.mass_bins = mass_bins

        # fit attributes
        self.an_to_mark = None
        self.mark_to_Y = None

    def _fit(self, am, y):

        an_train = get_an_from_am(am, self.mass_bins, mrange=self.mrange).reshape(-1)
        assert an_train.shape[0] == am.shape[0]

        y_sort, an_sort = self.cam_order * np.sort(self.cam_order * y), np.sort(an_train)
        marks = np.arange(len(y_sort)) / len(y_sort)
        marks += (marks[1] - marks[0]) / 2
        self.an_to_mark = interp1d(an_sort, marks, fill_value=(0, 1), bounds_error=False)
        self.mark_to_Y = interp1d(
            marks, y_sort, fill_value=(y_sort[0], y_sort[-1]), bounds_error=False
        )

    def _predict(self, am):
        an = get_an_from_am(am, self.mass_bins, mrange=self.mrange)
        return self.mark_to_Y(self.an_to_mark(an))


available_models = {
    "gaussian": MultiVariateGaussian,
    "cam": CAM,
    "linear": LinearRegression,
    "lasso": LASSO,
    "lognormal": LogNormalRandomSample,
}


def training_suite(data: dict):
    """Returned models specified in the data dictionary.

    Args:
        data:  Dictionary containing all the information required to train models. Using the format
            `name:info` where `name` is an identifier for the model (can be anything)
            and `info` is a dictionary with keys:
                - 'xy': (x,y) tuple containing data to train model with.
                - 'model': Which model from `available_models` to use.
                - 'n_features': Number of features for this model.
                - 'kwargs': Keyword argument dict to initialize the model.
    """
    # check data dict is in the right format.
    assert isinstance(data, dict)
    for name in data:
        assert isinstance(data[name]["xy"], tuple)
        assert data[name]["model"] in available_models
        assert isinstance(data[name]["n_features"], int)
        assert isinstance(data[name]["kwargs"], dict)
        assert data[name]["n_features"] == data[name]["xy"][0].shape[1]

    trained_models = {}
    for name in data:
        m = data[name]["model"]
        kwargs = data[name]["kwargs"]
        n_features = data[name]["n_features"]
        x, y = data[name]["xy"]
        model = available_models[m](n_features, **kwargs)
        model.fit(x, y)
        trained_models[name] = model

    return trained_models
