ROOT_DIR="/home/imendoza/alcca/nbody-relaxed"
OUTPUT="output_m12"
M_LOW=12.0
M_HIGH=12.2
N=10000
################# run pipeline #########################
./bin/catalog_pipeline.py --output-dir $OUTPUT make-ids --m-low $M_LOW --m-high $M_HIGH
--n-haloes $N
#./bin/catalog_pipeline.py --output-dir $OUTPUT make-dmcat
#./bin/catalog_pipeline.py --output-dir $OUTPUT make-subhaloes
#./bin/remote.py --cmd "./bin/catalog_pipeline.py --output-dir $OUTPUT make-progenitors"