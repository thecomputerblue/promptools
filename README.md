# promptools
teleprompter software for live music

This is my first app, which I began shortly after beginning to study python
in late 2020. It aims to solve some of the issues of teleprompting for music,
like dealing with large song libraries, different song arragements, choatic 
rehearsal environments, and the need to rapidly transpose music. These are 
problems I've dealt with for several years as a professional teleprompter, and
nothing on the market solves all of them in one place.

The gui is built with tkinter. I think the only thing used here outside of
standard python library stuff is striprtf. This is mac only, for now.
I haven't learned anything about dependency management but will get around
to it. In fact, me publishing this to github is "getting around to" learning
how to use github, so I'm sure this repo will become a nasty mess before long.
Just about everything detail of this project is "my first experience with x" so
expect some weirdness. I do my best to keep code readable and reduce coupling,
so hopefully the blind spots don't grind things to a halt (they have before,
repeatedly, and I've improved a lot from these experiences).

Almost nothing is implemented on the grand scale of planned features,
as I keep rewriting modules from scratch as I learn better practices.
The majority of buttons and menu options do nothing. In the next few months
I am hoping to get all the basic library mgmt, import and export working.
So far I've dipped my toes into a bunch of different problems with a "get
one of everything working" approach, and will go back to do all the rote 
implementation of solved problems in blocks, ie. spend a few days on all the
setlist buttons, librarian features, scroll behavior, editor undo stack, etc.

The very basic functions of a teleprompter are here - you can load text or
rtf files, and scroll them by holding SHIFT or toggle with spacebar.
The ',' and '.' keys smoothly page the view up and down a few lines.
You can drag around the focus arrow to your preferred position. The text and
arrow will scale to talent window size, and it can be made fullscreen on a 
second monitor. Eventually you will be able to scale the font yourself and 
choose a different monospaced font, customize colors, etc.

You can load txt or rtf files by dropping them in app/data/lib and starting the
app, then navigating to the Files tab at the bottom of the main window. 
Selecting a file will show a preview in the preview window with automatic 
color formatting. From there you can click the big button to load to the 
prompter, or go to Tools -> Transposer on the menubar and play with the song 
transposition. The search bar in this widget should also filter the file list.
You can also load whatever is previewed by pressing CMD+P, as long as you are
not in edit mode.

Once loaded you can edit a song in a rudimentary way by enabling edit mode
with CMD+E. The editor frame will change from green to yellow to indicate
scrolling is disabled, and that the talent view will follow your edits.
Some of the right click tagging options will change colors,
but this formatting is not consistently saved, as I need to write better
interfacing with tkinters text widget.

You can save your edits to the POOL or SETLIST with CMD+P or CMD+L
respectively. You can edit metadata on a selection in the right pane,
though almost none of this gets saved yet. The name does! This is all lost
at program exit but will eventually persist between runs.

You'll notice the setlist songs sometime appear highlighted. This is part of
an eventual system of navigating through setlists which I will explain in
future docs.

You can dump your setlist to a library database with DUMP SETLIST(TEMP)
in the Setlist menu up top (these other options don't do anything). These
can be recovered on subsequent runs.

You can view your song library via Library -> Browse. Nothing else is
implemented here, except "Cue selected song for playback" which will push
the song from db to the preview, where it can be loaded into the prompter. 
This setting also persists between runs of the program in a settings.json file
in the data folder. Eventually the other tabs will be used to manage setlists,
gigs, and various library behaviors.

I try to work on this a few hours every day, other obligations permitting. 
Hopefully ready for a proper 1.0 release mid 2022. If you are a teleprompter
let me know if there are any features you'd like to see prioritized. I am 
currently figuring out an orderly way to proceed on feature development, now 
that I've got a basic outline of where I want to go with this app. I am writing
a 'wishful' instruction manual for this which will give a preview of how
I expect this to operate in a year or two. I'll publish that sometime in the
near future.

Thanks for reading
- Joel

PS Use this at your own risk. Your computer probably won't explode but that's
above my pay grade (zero dollars). I would not recommend using this in a
professional environment yet. Try Presentation Prompter if you need something
stable and broadly useful, that's what I use for most gigs.
