import torch
import torchvision
from torchvision import transforms, utils
import torch.optim as optim
from torchvision import datasets
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch.nn as nn
import torch.nn.functional as F
from sklearn import metrics

from torch.utils.data import Dataset, DataLoader
import os
import time
IMGSIZE=300
IMG_RESIZE=300
IMGCHANNEL=3

torch.cuda.empty_cache()
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CLASSES = ('cherry', 'strawberry', 'tomato')

train_dir = "traindata/"

"""### Data Loader"""

class ImageFolderWithPaths(datasets.ImageFolder):

    def __getitem__(self, index):

        img, label = super(ImageFolderWithPaths, self).__getitem__(index)

        path = self.imgs[index][0]
        img_size = img.shape

        return (img, label ,path)

transform = transforms.Compose([
        transforms.Resize((IMG_RESIZE, IMG_RESIZE)),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

dataset = ImageFolderWithPaths(train_dir,transform=transform)

"""### Define function"""

def f_train(net, criterion, optimizer, train_set, batch_size=32, eval_set=None, epochs=100):
  train_loss =[]
  train_acc =[]
  eval_acc =[]

  if eval_set != None:
    val_loader = DataLoader(eval_set, batch_size=EVAL_BATCH_SIZE, shuffle=False)

  net.to(DEVICE)
  for epoch in range(epochs):  # loop over the dataset multiple times
      train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
      # print(epoch)
      start = time.time()
      running_acc = 0
      running_loss = 0.0
      for i, (data) in enumerate(train_loader, 0):

          inputs, labels, _ = data

          inputs = inputs.to(DEVICE)
          labels = labels.type(torch.LongTensor)
          labels = labels.to(DEVICE)

          # zero the parameter gradients
          optimizer.zero_grad()
          outputs = net(inputs)
          outputs = outputs.to(DEVICE)

          loss = criterion(outputs, labels)
          loss.backward()
          optimizer.step()

          _, pred = torch.max(outputs, 1)
          acc = torch.sum((pred==labels))

          # print statistics
          running_loss += loss.item()
          running_acc += acc.item()
      elapse = (time.time() - start)/60
      if eval_set != None:
        e_acc_total = 0
        with torch.no_grad():
          for i, (data) in enumerate(val_loader, 0):

            X, y, _ = data

            X = X.to(DEVICE)
            y = y.type(torch.LongTensor)
            y = y.to(DEVICE)
            o = net(X)
            _, pred = torch.max(o, 1)
            e_acc = torch.sum((pred==y))
            e_acc_total = e_acc_total + e_acc

      train_loss.append(running_loss / TRAIN_SIZE)
      train_acc.append(running_acc / TRAIN_SIZE)

      if eval_set != None:
        eval_acc.append(e_acc_total.item()/EVAL_SIZE)
        print(f'{(epoch + 1):<3} | elapse: {elapse:.1f} mins | train loss: {running_loss / TRAIN_SIZE:.3f} | train accuracy: {running_acc/TRAIN_SIZE:.3f} | Eval accuracy: {e_acc_total/EVAL_SIZE:.3f}')
      else:
        print(f'{(epoch + 1):<3} | elapse: {elapse:.1f} mins | train loss: {running_loss / TRAIN_SIZE:.3f} | train accuracy: {running_acc/TRAIN_SIZE:.3f}')
  
  file_name = 'model_resnet_' + str(round(time.time())) + '.pth'
  torch.save(net.state_dict(), file_name)
  print(f"Model is saved to {file_name}")

  return (train_loss, train_acc, eval_acc)

"""### Pretrain model"""

model_resnet =  torchvision.models.resnet18(weights='IMAGENET1K_V1')
num_ftrs = model_resnet.fc.in_features
model_resnet.fc = nn.Linear(num_ftrs, 3)

# for p in model_resnet.parameters():
#   p.requires_grad = False
# for param in model_resnet.fc.parameters():
#   param.requires_grad = True

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TRAIN_SIZE = len(dataset) #int(len(dataset.targets) * 0.75)
EVAL_SIZE = (len(dataset.targets) - TRAIN_SIZE)
EVAL_BATCH_SIZE = 32
BATCH_SIZE = 32
EPOCHS = 30
# train_set, eval_set = torch.utils.data.random_split(dataset, [TRAIN_SIZE, EVAL_SIZE])
train_set = dataset # no spliting

print(f"Train dataset size {TRAIN_SIZE} | Number of epochs: {EPOCHS}")

# model_resnet = model_resnet.to(DEVICE)
# summary(model_resnet, (IMGCHANNEL, IMG_RESIZE, IMG_RESIZE), BATCH_SIZE)

criterion = nn.CrossEntropyLoss()

optimizer_resnet = optim.SGD(model_resnet.parameters(), lr=0.001, weight_decay=0.01)

train_loss, train_acc, eval_acc = f_train(model_resnet, criterion, optimizer_resnet, train_set=train_set,
                                           batch_size=BATCH_SIZE, eval_set=None, epochs=EPOCHS)

# fig, ax1 = plt.subplots(figsize=(4, 4))

# ax2 = ax1.twinx()
# l1 = ax1.plot(range(1, EPOCHS+1), train_loss, 'r', label="Loss")
# l2 = ax2.plot(range(1, EPOCHS+1), train_acc, 'b', label="Training Accuracy")
# l3 = ax2.plot(range(1, EPOCHS+1), eval_acc, 'b', linestyle='--', label="Validation Accuracy")

# # added these three lines
# la = l1+l2+l3
# labs = [l.get_label() for l in la]
# ax1.legend(la, labs, loc=(1.2,0.8), fontsize=10)

# ax1.set_xlabel('Epoch')
# ax1.set_ylabel('Training Loss', color='r')
# ax2.set_ylabel('Accuracy', color='b')
# ax2.set_ylim(bottom = 0.5, top = 1)
# ax1.set_ylim(bottom = 0, top = 0.03)

# plt.title("Resnet18")

# evaluating
# val_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=False) #EVAL_SIZE
# y, preds = f_eval_result_batch(net4, val_loader)

"""### Save model"""

