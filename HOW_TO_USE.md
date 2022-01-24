# How to use MOSI

There are 3 main features of MOSI. MOS, AB(X) and SUS. All are based on uploading clips for others to evaluate.

## MOS tests
[MOS](https://en.wikipedia.org/wiki/Mean_opinion_score) tests are used to evaluate TTS clips on a scale of 1 to 5. The partitipant listens to a seiries of clips, and is prompted by a question like: "How natural does this voice sound?" and is asked to rate it on a scale of 1 to 5 bases on that. 

An admin of MOSI can navigate to the MOS tab in the header where they can click the button and create a new MOS test "Búa til MOS próf". You are then taken to a new empty MOS test. The rightmost button "Hlaða upp" is used for uploading audio clips. Once clicked window pops up describing the requirements for the upload. Please read the instructions about the uploading process and then download and examine the example. If you are in unfamiliar with this process you can to upload the example zip file straight away and see how it works. 

After uploading the audio the "ABtest-page" should be split into 2 parts. The first "Talgervingar sem búnar voru til" are the synthesised audio clips that were uploaded. You can tick the box by each clip to select if they are contained in the test at a given time. The next part of the page is similar but contains the recorded audio clips you uploaded(ground truth).

You can select the clips you want to be in the test and then send the test out.


Lastly there is the part called "Allar hljóðklippur" which simply display all uploaded audio clips. 

### Buttons at top

**Skoða niðurstöður:**
Opens a results page that as of yet displays very basic restults. There you can also download the restults of the test.

**Hlekkur á próf:**
Takes you to a form page for the test, this url you can send out to your partitipants. They fill out very basic information that is stored in the database.

**Hefja próf:**
Starts the test under your user. Mostly done for testing becase each user can only hand in on rating on each sentance so it gets overwritten if the same user takes the test many times.

**Sækja upptökur:**
Downloads the audiofiles you uploaded.

**Breyta stillingum:**
You can change some configurations of the test by clicking the leftmost button at the top called "Breyta stillingum". There you can fill in: 
* <code>Spruning</code> (a question) that is displayed at the top of the test like "Veldu það hljóðbrot sem þér finnst hljóma betur. 
* <code>Hjálpartexti</code> is displayed at the bottom of the test with your instructions if yout think you need them. 
* <code>Form texti</code> is displyed at the registeration form you send out to your partitipants.
* <code>Þakkartexti</code> is displayed at the end of the test to thank partitipants for their help.
* <code>Nota latin-square</code> is decides it a latin square method is used to cover the distirbution of audio clips to partitipants.
* <code>Sýna texta við hljóðbút</code> is a radio button that decides if the text of the audio is displayed for partitipants.




## AB tests 

[MOS](https://en.wikipedia.org/wiki/Mean_opinion_score) tests are used to evaluate TTS clips on a scale of 1 to 5. The partitipant listens to a seiries of clips, and is prompted by a question like: "How natural does this voice sound?" and is asked to rate it on a scale of 1 to 5 bases on that. 

An admin of MOSI can navigate to the MOS tab in the header where they can click the button and create a new MOS test "Búa til MOS próf". You are then taken to a new empty MOS test. The rightmost button "Hlaða upp" is used for uploading audio clips. Once clicked window pops up describing the requirements for the upload. Please read the instructions about the uploading process and then download and examine the example. If you are in unfamiliar with this process you can to upload the example zip file straight away and see how it works. 



After uploading the audio the "ABtest-page" should be split into 3 parts. The first "Setningar sem til skoðunar" is a list of the sentances available. You have to expand this part by clicking on the title. After that you can click on each sentence and prompt a dialog box where you can pick the tuple combination you want to evaluate. After picking a tuple it is sent to the next part of the "ABtest-page" called "ABpróf sem til skoðunar"(You might have to reload the page for them to show up). Here you can tick each radio button to pick which of them are active at the current time. 


Lastly there is the part called "Allar hljóðklippur" which simply display all uploaded audio clips. 

### Buttons at top

**Skoða niðurstöður:**
Opens a results page that as of yet displays very basic restults. There you can also download the restults of the test.

**Hlekkur á próf:**
Takes you to a form page for the test, this url you can send out to your partitipants. They fill out very basic information that is stored in the database.

**Hefja próf:**
Starts the test under your user. Mostly done for testing becase each user can only hand in on rating on each tuple so it gets overwritten if the same user takes the test many times.

**Sækja upptökur:**
Downloads the audiofiles you uploaded.

**Breyta stillingum:**
You can change some configurations of the test by clicking the leftmost button at the top called "Breyta stillingum". There you can fill in: 
* <code>Spruning</code> (a question) that is displayed at the top of the test like "Veldu það hljóðbrot sem þér finnst hljóma betur. 
* <code>Hjálpartexti</code> is displayed at the bottom of the test with your instructions if yout think you need them. 
* <code>Form texti</code> is displyed at the registeration form you send out to your partitipants.
* <code>Þakkartexti</code> is displayed at the end of the test to thank partitipants for their help.
* <code>Hámark setninga sem þáttakendur hlusta á</code> is to set a limit on how many sentences partitipants have to listen to. The default is 15.
* <code>Sýna texta við hljóðbút</code> is a radio button that decides if the text of the audio is displayed for partitipants.


## SUS tests
Fairly simple, you can just upload clips here and send out a link by clicking "Hlekkur á próf". This allows partitipants to see a list of the clips you uploaded.

## Management
Under "Notendur" header tab you can create other users like admin users, that can create tests.