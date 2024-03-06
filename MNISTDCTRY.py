# -*- coding: utf-8 -*-
"""MNIST GAN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pgto1OWYzRa0t9Qw59ALq1wLwiwoUAgf
"""

import sys
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import SGD, Adam
from tensorflow.keras.layers import Input , Flatten, Reshape, Conv2DTranspose, Dense, LeakyReLU, Dropout, BatchNormalization

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    # Restrict TensorFlow to only allocate 1GB of memory on the first GPU
    try:
        tf.config.experimental.set_virtual_device_configuration(gpus[0],
       [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=4096)])
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Virtual devices must be set before GPUs have been initialized
        print(e)

#loading dataset
data=tf.keras.datasets.mnist
(xtrain,ytrain),(xtest,ytest)= data.load_data()

xtrain,xtest=xtrain/255.0 *2 -1, xtest/255.0 * 2 -1

n,h,w=xtrain.shape
d=h*w
xtrain=xtrain.reshape(-1,d)
xtest=xtest.reshape(-1,d)
print(n,h,w,d)

#Dimensionality of latent space
latent_dim=100

#Generator

def build_generator(latent_dim):
    # Input layer
    i = Input(shape=(latent_dim,))
    
    # Project and reshape
    x = Flatten()(i)
    x = Dense(128 * 7 * 7)(x)
    x = Reshape((7, 7, 128))(x)
    
    # Transposed convolution layers
    x = Conv2DTranspose(128, kernel_size=4, strides=2, padding='same')(x)
    x = LeakyReLU(alpha=0.2)(x)
    x = BatchNormalization()(x)
    
    x = Conv2DTranspose(64, kernel_size=4, strides=2, padding='same')(x)
    x = LeakyReLU(alpha=0.2)(x)
    x = BatchNormalization()(x)
    
    # Output layer
    x = Conv2DTranspose(1, kernel_size=7, activation='tanh', padding='same')(x)

    # Model
    model = Model(i, x)
    return model
  
# Discriminator
inputshape=(28,28,1)
def build_discriminator(inputshape):
    # Input layer
    i = Input(shape=(inputshape))
    
    # Project and reshape
    x = Dense(128 * 7 * 7)(i)
    x = Reshape((7, 7, 128))(x)
    
    # Transposed convolution layers
    x = Conv2DTranspose(128, kernel_size=4, strides=2, padding='same')(x)
    x = LeakyReLU(alpha=0.2)(x)
    x = BatchNormalization()(x)
    
    x = Conv2DTranspose(64, kernel_size=4, strides=2, padding='same')(x)
    x = LeakyReLU(alpha=0.2)(x)
    x = BatchNormalization()(x)
    
    # Flatten layer
    x = Flatten()(x)
    
    # Dense layer
    x = Dense(7 * 7 * 128, activation='relu')(x)
        # Output layer
    x = Reshape((7, 7, 128))(x)

    # Transposed convolution layers
    x = Conv2DTranspose(1, kernel_size=4, strides=2, padding='same', activation='tanh')(x)

    # Model
    model = Model(i, x)
    return model

#compiling both models

#build discriminator and compile with BCE
disc=build_discriminator(d)
disc.compile(loss='binary_crossentropy',optimizer=Adam(0.002,0.5),metrics=['accuracy'])

#initiate generator
gen=build_generator(latent_dim)

#create input for noise sample from latent space
z=Input(shape=(latent_dim,))

#input to generator
img=gen(z)

#freeze discriminator layers
disc.trainable=False

#true output is fake and we label it as real
fake_pred=disc(img)

#final combined model
combined_model=Model(z,fake_pred)

#compiling the model
combined_model.compile(loss='binary_crossentropy',optimizer=Adam(0.0002,0.5))

#Training the GAN

#initializing values
batch_size=2
epochs=300000
sample_period=3000 #generate and save some data every sample period

#batch labels
ones=np.ones(batch_size)
zeros=np.zeros(batch_size)

#saving the loss values
dloss=[]
gloss=[]

#saving gan images
if not os.path.exists(r'C:\Users\abhiu\Desktop\college stuff\sem 6\Deep Learning\gan_images'):
  os.makedirs(r'C:\Users\abhiu\Desktop\college stuff\sem 6\Deep Learning\gan_images')

#function to generate a grid of random samples from the generator and save in a file
def sample_images(epoch):
  rows,cols=5,5
  noise=np.random.randn(rows * cols, latent_dim)
  img=gen.predict(noise)

  #rescale img
  img=0.5* img + 0.5

  fig,axs=plt.subplots(rows,cols)
  idx=0
  for i in range(rows):
    for j in range(cols):
      axs[i,j].imshow(img[idx].reshape(h,w),cmap='gray')
      axs[i,j].axis('off')
      idx+=1
  fig.savefig(r"C:\Users\abhiu\Desktop\college stuff\sem 6\Deep Learning\gan_images\MNIST_DCGAN\%d.png" %  epoch)
  plt.close()

#main training loops
d_losses,g_losses=[],[]
for epoch in range(epochs):

  #train Discriminator

  #select a random batch of images
  idx=np.random.randint(0,xtrain.shape[0], batch_size)
  real_imgs=xtrain[idx]

  #generate fake images
  noise=np.random.randn(batch_size,latent_dim)
  fake_imgs=gen.predict(noise)


  #train the discriminator, loss & accuracy are returned
  d_loss_real,d_acc_real=disc.train_on_batch(real_imgs,ones)
  d_loss_fake,d_acc_fake=disc.train_on_batch(fake_imgs,zeros)
  d_loss=0.5*(d_loss_real+d_loss_fake)
  d_acc= 0.5*(d_acc_real+d_acc_fake)


  #train generator
  noise=np.random.randn(batch_size,latent_dim)
  g_loss=combined_model.train_on_batch(noise,ones)

  #save the loss
  d_losses.append(d_loss)
  g_losses.append(g_loss)

  if epoch%100==0:
    print(f"epoch: {epoch+1}/{epochs}, d_loss:{d_loss:.2f}, \
    d_acc: {d_acc:.2f}, g_loss:{g_loss:.2f}")

  if epoch%sample_period==0:
    sample_images(epoch)
  

combined_model.save_weights(r'C:\Users\abhiu\Desktop\college stuff\sem 6\Deep Learning\gan\weights')
combined_model.save(r'C:\Users\abhiu\Desktop\college stuff\sem 6\Deep Learning\gan')

plt.plot(g_losses,label='generator loss')
plt.plot(d_losses, label='discriminator loss')
plt.legend()

