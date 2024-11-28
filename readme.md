# image classifier

My take on an image classifier, uses tensorflow and keras libraries for model training.

## Installation
The project was developed in windows 10 using [WSL2](https://learn.microsoft.com/en-us/windows/wsl/about#what-is-wsl-2) and a [conda](https://anaconda.org/anaconda/conda) virtual environment.

create and update a conda environment:
```bash
conda env update --name your_env_name --file environment.yml
```

activate the conda env:
```bash
conda activate your_env_name
```

### Trouble installing
Ran into some errors while installing nvidia cuda libraries and for my setup found the following solutions (obligatory YMMV):

Main error https://github.com/keras-team/tf-keras/issues/62

Solution found here https://github.com/keras-team/tf-keras/issues/62#issuecomment-1730880378

```bash
# Install NVCC
conda install -c nvidia cuda-nvcc=11.3.58
# Configure the XLA cuda directory
mkdir -p $CONDA_PREFIX/etc/conda/activate.d
printf 'export XLA_FLAGS=--xla_gpu_cuda_data_dir=$CONDA_PREFIX/lib/\n' >> $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
source $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
# Copy libdevice file to the required path
mkdir -p $CONDA_PREFIX/lib/nvvm/libdevice
cp $CONDA_PREFIX/lib/libdevice.10.bc $CONDA_PREFIX/lib/nvvm/libdevice/
```
### Building the frontend
```
cd ./frontend
npm run build
```

## Usage

Once installed, activate the conda environment
```bash
conda activate your_env_name
```

Run the flask server
```
python app.py
```
Note: This is a personal project meant to run locally and only when required so there was no need for a proper server, proxy config etc.

The image files to be processed should be placed in `./data/images/input` from there, accessing `localhost:5000` from a browser will bring us to the main page, where one can select a 'session' sessions are automatically created when images are added to the folder mentioned before.

The classification is meant to be done by hand, once `batch_size` (32) or more images are labelled, one can train the model for the first time (click on `Train Full`). After that the model can be retrained in full or fine-tuned when more images are labeled.

After training the model, the UI will recommend the labels for the following images with a '👇' emoji. The images will be recommended in groups so one does not have to move the hand as much.

Finally, by clicking on `Move labeled images` the labelled images are moved to the output folders grouped by label.



## Screenshots
![Session Selector](/readme_imgs/c1.jpg)
![Classifier](/readme_imgs/c2.jpg)


Note: I am aware that there are open source and freemium alternatives that can sort and label images on a larger scale like immich, and also data storage costs often go down. But this project the way I imagine an image classifier for not a great amount of images, just the ones I have.