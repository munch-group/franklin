## Franklin commands-  Students version
### Activate franklin
To use franklin activate the enviroment were you installed franklin. If you followed the installationguide that enviroment should be called franklin. In order to activate the enviroment use the command below:

conda activate franklin

Then navigate to an empty folder by using the terminal (remember you can use the cd to enter a subfolder, ls to see what is in the subfolder and cd .. to go back to main folder)

After activating your franklin enviroment you can then type franklin in your terminal in order to see the different options in franklin. It should look like this: 
![alt text](<images/Skærmbillede 2025-05-28 kl. 14.37.28.png>)

### Download and open exercises
In order to use the commands listed you will first have to type franklin. Thats means if you want to use the download command you will in your terminal write 

franklin download

You will use this command when you want do download an exercise. After running this command a selection menu will pop out and in this menu you will be able to pick between the different courses.
![alt text](<images/Skærmbillede 2025-05-28 kl. 14.52.02.png>)

You choose your course by using the arrow keys and a new selection menu will appear where you can select the specific exercise that you want to do. Franklin then places the downloaded assignment in your the empty folder where you first started franklin. Now before you can do the next step you will have to go to the exercise folder you just downloaded (use cd folder_name_of_exercise)

Then in order to make sure can run code in the exercise you run the command:

franklin jupyter 

A new selection menu now opens that once more shows you the different courses. Use the key arrows to pick your course and in the submenu pick the exercise you want to solve. Jupyter notebook now opens in your browser. in the filemenu on the right side in jupyter you should be able to see your newly downloaded exercise. Open it and your ready to go!

Note: If the message below pops up, the folder you started franklin in was either not empty or you may have forgotten to go to the exercise subfolder![alt text](<images/Skærmbillede 2025-05-28 kl. 15.22.07.png>)

### Clean up old docker containers
In order or your TØ exercises to run correctly an enviroment that is the same for each students computer is created in docker. These are also specific for each course and exercise. Unfortunately, these take up a fair ammount of space on your computer, so when you are done with a course it might be a good idea to delete these. 

You can easily do this by using the command franklin cleanup

run the command: 
franklin cleanup

A seletion menu will then appear with all your currently downloaded docker images, named after each of your exercises. You can then use your arrow keys to select the exercise enviroments that you no longer use. 

![alt text](<images/Skærmbillede 2025-05-28 kl. 15.32.16.png>)

Note: deleting the exercise enviroments like this DO NOT delete the exercise you have made yourself and of you would ever need a specific enviroment for an old exercise again, you simple download it once more.

### Update franklin
Franklin should update automaticaly when you start the program, but if you should need to update it manually you can use the command 

franklin update

You can also check out which version of franklin you have installed by using the command 

franklin --version


## Educators version

The educators version of franklin looks a lot like the student version with extra features for creating and editing exercises. 

### Make a new exercise via franklin 
To create a new exercise you will need to use the command 

franklin exercise

When you run this command a new page of commands will show. 
![alt text](<images/Skærmbillede 2025-05-29 kl. 16.19.09.png>)

In order to create a new exercise you use the command 

franklin exercise new

A selection menu then appears and you choose the course you want to make an exercise for. Franklin then asks you to make make a short descriptive label of your exercise. This will be the title of the exercise. When you have named your exercise press enter

...... MANGLER

### Edit an already existing exercise
To edit an exercise use the command

franklin exercise edit

and choose your course and exercise you want to edit in the selection menu. 

.....MANGLER

### download an exercise without editing.

If you want to download an exercise the same way the students does it, you can use the command

franklin download

After running this command a selection menu will pop out and in this menu you will be able to pick between the different courses.
![alt text](<images/Skærmbillede 2025-05-28 kl. 14.52.02.png>)

You choose your course by using the arrow keys and a new selection menu will appear where you can select the specific exercise that you want to download. Franklin then places the downloaded assignment in your the empty folder where you first started franklin. Now before you can do the next step you will have to go to the exercise folder you just downloaded (use cd folder_name_of_exercise)

Then in order to make sure can run code in the exercise you run the command:

franklin jupyter 

A new selection menu now opens that once more shows you the different courses. Use the key arrows to pick your course and in the submenu pick the exercise you want to solve. Jupyter notebook now opens in your browser. in the filemenu on the right side in jupyter you should be able to see your newly downloaded exercise. Open it and your ready to go!

Note: If the message below pops up, the folder you started franklin in was either not empty or you may have forgotten to go to the exercise subfolder![alt text](<images/Skærmbillede 2025-05-28 kl. 15.22.07.png>)

### Rename an exercise

### Gitui

franklin exercise gitui lances git GUI 

Git gui opens up a page with 4 section: unstaged changes, staged changed commit box and modified, not staged.

Git gui can be used for version control, meaning if you an another educator is editing the same exercise at the same time, Git Gui can help you select which changes you want to keep, if you have editet the exact same assignment or it will allow you to merge both your changes into the new version of the assignment

### Clean up old docker containers
In order or your TØ exercises to run correctly an enviroment that is the same for each students computer is created in docker. These are also specific for each course and exercise. Unfortunately, these take up a fair ammount of space on your computer, so when you are done with a course it might be a good idea to delete these. 

You can easily do this by using the command franklin cleanup

run the command: 
franklin cleanup

A seletion menu will then appear with all your currently downloaded docker images, named after each of your exercises. You can then use your arrow keys to select the exercise enviroments that you no longer use. 

![alt text](<images/Skærmbillede 2025-05-28 kl. 15.32.16.png>)

Note: deleting the exercise enviroments like this DO NOT delete the exercise you have made yourself and of you would ever need a specific enviroment for an old exercise again, you simple download it once more.

### Update franklin
Franklin should update automaticaly when you start the program, but if you should need to update it manually you can use the command 

franklin update

You can also check out which version of franklin you have installed by using the command 

franklin --version


## Make a new exercise directly in gitlab

You can also edit and make new exercises directly in gitlab
To do this go to the gitlab website and find the repository with your course. This can be done by clicking on your profile and then choosing "my repositories" in the selection menu. Then choose tbe course you want to create and assignment for and click on new re

Hvordan får man det så ind i franklin?

Hvad gør man med de pakker med gerne vil bruge?
- Var det det med templates hvor vi så bare laver basic pakker de henter ned og så 


