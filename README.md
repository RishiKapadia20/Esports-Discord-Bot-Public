# Esports-Discord-Bot-Public

During the summer I was voted as treasure of the Esports society and one of my responsibilities was to manage and maintain our discord server (discord is very similar to slack but for gamers). And with the new term starting soon, we would have to manually assign everyone correct tags based on the games they play and be able to verify that they were members of our society. With our society usually consisting of 150+ members this is extremely time costly to do manually. 

Over the I developed a discord bot. I developed the bot in python using the discord python library and using google sheets as a database. Now usually I wouldn't use google sheets as a database solution however I wanted people’s gamer information such as in game names and competitive ranks to be visible to all members as this makes it easier for members to find other members to build teams or play together. The main functionality of the bot is the signup command, which triggers the bot to message a user for a bunch of details. Once it gets the details it uploads all relevant information to a google doc and assigns that user with the correct tags.

Once I finished with the main feature I came up and added some side features which would make my life as a discord admin a lot easier. One of the most useful features is the broadcast command. Usually when you want to communicate with a group of people you would ‘@’ them on discord. However, when you message them in a text channel it can get lost with other messages. So, the broadcast function takes in a tag and a message and the bot would direct message every user with that tag that message. This makes it more likely for a user to see a message from an admin.

I hosted my bot in an AWS EC2 instance so that it was running 24/7. The bot was quite successful as it was able to handle most users and very little time was spent from the Admins having to manually add tags. There were a few bugs which caused a lot of problem initially such as my use of google sheets api wasn’t efficient, therefore hitting the request/sec cap after a few uses. However, I was able to identify and find a solution. Currently the bot is running on our discord server with no known issues.

I found this project extremely fun as it was a real-world problem for me where I was able to solve it using my programming skills. It gives me belief that any more problems in life I will be able to find a cool and fun solution using my programming skills.

List of Commands:

* !signup: will ask the user a series of questions to set up correct server roles 
* !cleanup: manual removal of unverified users
* !unverified: lists all users in the server that are unverfied
* !invlink: creates a temporary invite link that can only be used once
* !broadcast: direct messages everyone with a specific role with a message
* !verify: checks to see if you are a member and updates your tag
* !lolstats: takes a snapshot of your recent statistics. *Example:* `!lolstats EUW best_ign`
* !updateranks: updates your competitive ranks in the esports google doc
* updatelol: updates your League of Legends in game name on google doc *Example:* `!updatelol SKT Faker \n!sports-role: adds sports-irl role`
