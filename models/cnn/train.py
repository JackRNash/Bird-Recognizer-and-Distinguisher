import torch
import torch.nn as nn
import torch.nn.functional as Activation
import torch.optim as optim
import numpy as np
import torchvision
import matplotlib.pyplot as plt
import time
import os
import copy

from sklearn.metrics import confusion_matrix
from torchvision import datasets, models, transforms
from tqdm import tqdm

torch.manual_seed(4701)
np.random.seed(4701)

data_dir = '../../dataset/'
net_dir = './lenet5.pth'
batch_size = 8
num_epochs = 5


class Net(nn.Module):
    """
    This class represents a basic model of the Lenet-5 CNN modified to operate on
    256 x 256 images.

    CITATION: This class and its methods were taken and adapted from the following
        source: https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html
    """

    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 18, 5)
        self.pool1 = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(18, 54, 5)
        self.pool2 = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(61 * 61 * 54, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, val):
        """
        Returns the prediction corresponding to a given input image.

        Parameter val: the image to predict
        Precondition: val is 256x256x3 Torch Tensor object
        """
        val = self.pool1(Activation.relu(self.conv1(val)))
        val = self.pool2(Activation.relu(self.conv2(val)))
        val = val.view(-1, 61 * 61 * 54)
        val = Activation.relu(self.fc1(val))
        val = Activation.relu(self.fc2(val))
        val = self.fc3(val)
        return val


def calc_mean_std(dataloader):
    """
    Returns a list of the average RGB values and a list of the standard of
    the RGB values.

    Extracts the mean and standard of RGB values of every image in dataloader
    and then returns the average.

    Parameter dataloader: images to find the mean and standard of
    Precondition: dataloader is a Torch dataloader object

    CITATION: This function was taken and adapted from the following source:
        https://forums.fast.ai/t/image-normalization-in-pytorch/7534/7
    """
    mean = []
    std = []

    # Find and append the mean and standard of each image in dataloader
    for data in dataloader:
        img, _ = data

        batch_mean = torch.mean(img, (0, 2, 3))
        batch_std = torch.std(img, (0, 2, 3))

        mean.append(batch_mean)
        std.append(batch_std)

    # Find and return the mean and standard of every image in dataloader
    mean = np.mean([m.numpy() for m in mean], axis=0)
    std = np.mean([s.numpy() for s in std], axis=0)

    return mean, std


def preprocess_data():
    """
    Returns the transformation necessary to normalize the image data.

    Creates a normalization transformation that results in the training data
    having a mean of 0 and a standard deviation of 1.
    """
    transform = transforms.Compose([
        transforms.ToTensor()
    ])

    # Creates a dataloader object for the training and validation sets
    train_dataset = datasets.ImageFolder(os.path.join(data_dir, 'train'),
                                         transform)
    train_dataloader = torch.utils.data.DataLoader(train_dataset,
                                                   batch_size=batch_size, shuffle=True, num_workers=4)

    mean, std = calc_mean_std(train_dataloader)

    return transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean, std)
    ])


def train_model(dataloader, opt, val_dataloader):
    """
    Trains the CNN on the training data.

    Parameter dataloader: images used to train the CNN
    Precondition: dataloader is a Torch dataloader object

    Parameter opt: optimizer used to update the CNN after each pass
    Precondition: opt is a Torch optim object

    CITATION: This function was taken and adapted from the following source:
        https://forums.fast.ai/t/image-normalization-in-pytorch/7534/7
    """
    for epoch in range(num_epochs):
        total_train = 0
        correct_train = 0
        total_val = 0
        correct_val = 0
        for data in dataloader:
            imgs, labels = data

            # Zero the parameter gradients
            opt.zero_grad()

            # Perform forward-backward pass, then update optimizer
            outputs = net(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            opt.step()
            _, predicted = torch.max(outputs.data, 1)
            total_train += labels.nelement()
            correct_train += predicted.eq(labels.data).sum().item()
            train_accuracy = 100 * correct_train / total_train
        for data in val_dataloader:
            imgs, labels = data

            # Zero the parameter gradients
            opt.zero_grad()

            # Perform forward-backward pass, then update optimizer
            outputs = net(imgs)
            loss_val = criterion(outputs, labels)
            # loss_val.backward()
            _, predicted = torch.max(outputs.data, 1)
            total_val += labels.nelement()
            correct_val += predicted.eq(labels.data).sum().item()
            val_accuracy = 100 * correct_val / total_val
        print(train_accuracy)
        print(val_accuracy)
        print('Epoch {}, train Loss: {:.3f}'.format(epoch, loss.item()),
              "Training Accuracy: %d %%" % (train_accuracy), 'Epoch {}, val Loss: {:.3f}'.format(epoch, loss_val.item()), "Val Accuracy: %d %%" % (val_accuracy))


def test_model(net, dataloader):
    """
    Calculates the accuracy of the CNN on an unseen dataset.

    Parameter net: the CNN trained on the training data, used for bird
    classification
    Precondition: net is a Net object

    Parameter dataloader: images used to validate the CNN
    Precondition: dataloader is a Torch dataloader object

    CITATION: This function was taken and adapted from the following source:
        https://forums.fast.ai/t/image-normalization-in-pytorch/7534/7
    """
    correct = 0
    total = 0
    with torch.no_grad():
        for data in dataloader:
            imgs, labels = data
            outputs = net(imgs)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            for i in range(len(predicted)):
                if predicted[i] == labels[i]:
                    correct += 1
    print(100 * correct / total)
    print('Accuracy of the network on the ' + str(total) +
          ' test images: %d %%' % (100 * correct / total))


def plot_confusion_matrix(true, preds, classes, title):
    """
    Plots a confusion matrix based on predictions vs actual results.

    Creates a confusion matrix for all [classes] and saves it to plt.

    Parameter true: correct classifications
    Precondition: a list of integer classifications

    Parameter preds: predicted classifications
    Precondition: a list of integer classifications

    Parameter classes: all possible predictions
    Precondition: a list of strings

    Parameter title: title for the graph
    Precondition: a string
    """
    cmatrix = confusion_matrix(true, preds)
    threshold = np.min(np.diagonal(cmatrix))
    fig, ax = plt.subplots()
    ax.set(xticks=np.arange(cmatrix.shape[1]),
           yticks=np.arange(cmatrix.shape[0]),
           xticklabels=classes,
           yticklabels=classes)
    ax.set_ylabel('True label', fontsize=22)
    ax.set_xlabel('Predicted label', fontsize=22)
    ax.set_title(title, fontsize=22)
    ax.tick_params(axis='x', labelrotation=90)
    for i in range(cmatrix.shape[0]):
        for j in range(cmatrix.shape[1]):
            if cmatrix[i, j] > 0:
                ax.text(j, i, cmatrix[i, j], ha='center', va='center',
                        size=22, color='white' if cmatrix[i, j] < threshold else 'black')
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontsize(15)
    fig.set_size_inches(18.5, 10.5)
    fig.tight_layout()
    ax.imshow(cmatrix)


def get_labels_and_predictions(model, dataloader, device):
    preds, labels = [], []
    for data, label in tqdm(dataloader):
        data = data.to(device)
        output = model(data)
        _, pred = torch.max(output, 1)
        if len(label) != len(pred):
            print('UH OH', len(label), len(pred), label, pred)
        labels.append(label.detach().numpy())
        preds.append(pred.cpu().detach().numpy())
    preds = np.concatenate(preds, axis=0)
    labels = np.concatenate(labels, axis=0)
    return preds, labels


if __name__ == '__main__':
    # Obtain necessary transformation code
    data_transform = preprocess_data()

    # Create training and validation datasets
    image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir,
                                                           x if x != 'val' else 'validation'), data_transform)
                      for x in ['train', 'val', 'test']}
    # Create training and validation dataloaders
    dataloaders_dict = {x: torch.utils.data.DataLoader(image_datasets[x],
                                                       batch_size=batch_size, shuffle=True, num_workers=0)
                        for x in ['train', 'val', 'test']}

    # Create model
    net = Net()

    # Create loss function & establish optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)
    start_time = time.time()
    train_model(dataloaders_dict['train'], optimizer, dataloaders_dict['val'])
    print("Time taken: ")
    print("--- %s seconds ---" % (time.time() - start_time))
    epochs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    t_a = [25.35, 37.86, 52.28, 60.49, 73.26,
           85.54, 92.59, 96.21, 99.06, 96.25]
    v_a = [32.64, 42.62, 45.95, 44.28, 50.73,
           50.10, 49.90, 48.86, 51.77, 50.52]
    t_l = [1.688, 1.328, 1.694, 0.716, 1.103, .474, .162, .089, .003, 1.129]
    v_l = [1.876, 1.129, 0.876, 1.142, .336, .173, .785, 3.857, .004, .019]
    """ Remove this store/load functionality eventually """
    # Store model
    torch.save(net.state_dict(), net_dir)

    # Load model
    net = Net()
    net.load_state_dict(torch.load(net_dir))

    test_model(net, dataloaders_dict['val'])

    print("Testing: ")
    test_model(net, dataloaders_dict['test'])

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    net = net.to(device)

    val_preds_full, val_true_full = get_labels_and_predictions(net,
                                                               dataloaders_dict['test'], device)
    train_preds_full, train_true_full = get_labels_and_predictions(net,
                                                                   dataloaders_dict['train'], device)
    plot_confusion_matrix(val_true_full, val_preds_full,
                          image_datasets['test'].classes, "Test Confusion Matrix for CNN")
    plt.savefig('first_conf.png')
    # plot_confusion_matrix(train_true_full, train_preds_full,
    #                       image_datasets['train'].classes)
    # plt.savefig('second_conf.png')
    # plt.clf()
    # plt.plot(epochs, [(100-x) for x in t_a], 'r', label="training")
    # plt.plot(epochs, [(100-x) for x in v_a], 'b', label="validation")
    # plt.axis([1, 10, 0, 100])
    # plt.xlabel("Number of Epochs", fontsize=12)
    # plt.ylabel("Error", fontsize=12)
    # plt.title("Train vs Validation Error", fontsize=15)
    # plt.legend(loc="upper right")
    # plt.savefig('cnn_acc.png')
    # plt.clf()
