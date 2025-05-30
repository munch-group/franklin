## Get started with jupyter note book

### Install Anaconda Navigator
To run Jupyter notebook we will use a distribution of Python called Anaconda. Anaconda is the easiest way of installing Python on Windows, macOS (Mac), and Linux. To install Anaconda, head to [this](https://www.anaconda.com/download) site. Click "Download". When the download has completed, double-click the file you just downloaded and follow the instructions on the screen. It is important that you accept all the suggested installation settings.

### The terminal
You also need a tool to open files and start jupyter notebook. It is also here that you will run franklin in order to download exercises. The terminal will already be installed and is called Terminal on OSX and Anaconda powershell on mac. When you open the terminal it should look like fig 1.1 on mac and fig 1.2 on windows'

![Figure 1.1](<images/Skærmbillede 2025-05-22 kl. 16.44.43.png>)

![Figure 1.2](<images/Skærmbillede 2025-05-22 kl. 16.45.05.png>)

What is Anaconda powershell and this Terminal thing, you ask. Both programs are what we call terminal emulators. They are programs used to run other programs, like the ones you are going to write yourself. In this guide both Terminal and Anaconda Powershel will be refered to as "the terminal"

### Navigating folders via the terminal
The terminal is a very useful tool. To use it, howevever, you need to know a few basics. First of all, a terminal lets you execute commands on your computer. You simply type the command you want and then hit enter. The place where you type is called a prompt. 

When you open the terminal you'll be located in a folder you are in by typing pwd and then press Enter on the keyboard. When you press Enter you tell the terminal to execute the command you just wrote. In this case, the command you typed simply tells you the path to the folder we are in. It would look something like this:

pwd
/Users/kasper/programming 

If the path above was your output you would be in the folder programming. /Users/kasper/programmingis the path or "full address" of the folder with dashes (or backslashes on windows) separating nested
folders. So programmingis a subfolder of kasper which is a subfolder of Users. That way
you not only know which folder you are in but also where that folder is. Let us see what
is in this folder. On OSX you type the ls command (l as in Lima and s as in Sierra)

ls
notes 
projects

It seems that there are two other folders, one called notes and another called projects. If you are curious about what is inside the notes folder, you can "walk" into the folder with the cd command. To use this command you must specify which folder you want to walk into (in this case notes). We do this by typing cd, then a space and the then name of the folder. When you press enter you then get:

cd notes


It seems that nothing really happened, but if I run the pwd command  now to see which folder I am in, I get:

pwd
/Users/kasper/programming/notes

## Enviroments

### 
In bioinformatics, we install packages and programs so we can use them in our analyses and pipelines. Sometimes, however, the versions of packages you need for one project conflicts with the versions you need for other projects that you work on in parallel. Such conflicts seem like an unsolvable problem. Would it not be fantastic if you could create a small insulated world for each project, which then only contained the packages you needed for that particular project?. If each project had its own isolated world, then there would be no such version conflicts. Fortunately, there is a tool that lets you do just that, and its name is Conda.

“Conda is an open source package management system and environment  management system for installing multiple versions of software packages and their dependencies and switching easily between them. ”

The small worlds that Conda creates are called "environments". You can create as many environments as you like, and then use each one for a separate bioinformatics project, a course, a bachelor project, or whatever you would like to insulate from everything else. Conda also downloads and installs the packages for you and it makes sure that the software packages you install in each environment are compatible. It even makes sure that packages needed by packages (dependencies) are also installed. Conda is truly awesome.

In this case you need to create a new enviroment where you install franklin

You will need franklin for downloading assignments. You will also be able to choose a enviroment in franklin that specifially fits the assignment you want to make.

### Create Franklin enviroment and install franklin
In order to download franklin and install an enviroment called franklin you have to write the code below into your terminal

conda create -y -n franklin -c conda-forge -c munch-group franklin

This commands runs the Conda program and tells it to create a new enviroment with the name franklin and to install franklin in that enviroment. Once you have ran the command, your terminal output should look something like this:

[output](<images/Skærmbillede 2025-05-25 kl. 15.19.24.png>)

## Franklin for educators
You will then also need to download franklin educator 
Before you insert the code below, activate your franklin enviroment in your terminal 

conda activate franklin

conda install -c conda-forge -c munch-group franklin franklin-educator

## set up gitlab

### sign in
Go to gitlab by following [this link](https://gitlab.au.dk)
On the sign-in page, choose the login option called login with Uni-add. 

### SSH keys - what is that and why do i need it?
SSH keys are a secure way to log in to remote systems or services without needing to enter a password each time. An SSH key works like a digital lock and key system. The private key is kept safely on your computer, while the matching public key is shared with the service you want to access. When you try to connect, the service checks that your private key matches the public one it has on file. If they match, access is granted automatically—no password required.

### How do i get a SSH key?

kaspers guide

### insert SSH key to gitlab
To access your SSH keys you use the command: 
cat ~/.ssh/id_rsa.pub

It is very important that you choose the rsa.pub version.

After you have run the command cat ~/.ssh/id_rsa.pub in your terminal  a long line of letters and number will appear in your terminal. This is your SSH key. 
Now copy it and go back to the [gitlab webpage](https://gitlab.au.dk) 

Then press the icon on the top beside the picture that represent your profile and find the option called "edit profile" in the dropdown menu
It should look like this: ![alt text](<images/Skærmbillede 2025-05-27 kl. 13.42.11.png>)

Now you should be able to see an option in the left side menu called ‘add new ssh key’. You press that and then you insert the copied ssh-key in the box.

The page should look something like the figure below:
![alt text](<images/Skærmbillede 2025-05-27 kl. 13.40.10.png>)

In the bottom of the page, you can write an expiration date of your SSH key. In order to not have to enter a new SSH key, you can remove this. 

You are now ready to use gitlab!

## How do i create a new assignment

## jupyter lab

### What can i do in jupyter lab?
JupyterLab is an easy-to-use program that helps you learn and work with code. You open it in a web browser, and it lets you write code, run it, and see the results right away.

It’s especially useful for trying out small bits of code, doing calculations, looking at data, and making plots. In juputer you can both write notes code and also run  the code, all on the same page.

### Markdown cells
There is two different kinds of cells in jupyter - markdown cells and code cells. In markdown cells you can write code in the same manner as you would in a teksteditor such as word. In markdown cells you can create a nice layout of your text piece. If you want to learn more check out the [jupyter guide notebook](<../../../../Jupyter Notebook Guide.ipynb>)

### Code cells
As the name implies you can write code in code cells and then execute your code by directly in jupyter lab by pressing shift+enter. 
If you want to see examples of what for example can be done in code cells check out the [jupyter guide notebook](<../../../../Jupyter Notebook Guide.ipynb>)

In order to make a new cell in markdown press the + icon on the right side of the cell. You can also use the shortcut "a" to make a cell above the cell you are interacting with, and you can use the shortcut "b" to create new cell below the one you were interacting with. If you have clicked the code cell so that you are able to write in it, you need to press esc prior to using the shortcuts. 

### create a new cell 
When you have a new cell you can choose whether you want it to be a markdown cell or a code cell by using the menu bar at the top of the page. In the example below, the current cell type is code. If you wanted to change it, you click where it says code, and then chooses markdown in the drop down menu: 
![alt text](<images/Skærmbillede 2025-05-27 kl. 13.39.22.png>)

You can also use the shortcut esc + m to change a code cell to a markdown cell, and esc+ y to change a markdown cell to a code cell. 