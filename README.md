# promptools
Teleprompter software for live music.

This is my first app, which I began shortly after beginning to study python
in 2020, when there was suddenly no work in the music industry for some reason.
It aims to solve some of the issues of teleprompting for music,
like dealing with large song libraries, different song arragements, choatic 
rehearsal environments, and the need to rapidly transpose and format music.
These are problems I've dealt with for several years as a professional
teleprompter, nothing I've found solves them all in one place, and a
few aren't solved anywhere!

The gui is built with tkinter. I plan to port it to kivy or pyqt once I'm
happy with the feature set. Most features are not strongly coupled with
tkinter so this shouldn't be a huge undertaking.

The only package used here outside of standard python library stuff is
striprtf. This is mac only, for now.

Currently this works as a basic teleprompter. There is a transposer in the
menu bar which pretty much works, though it's not currently detecting 'A'
chords correctly. This is a regression I find deeply disturbing, and I will
get around to fixing shortly.

Some important key commands:
CMD + p = load cued song to prompter
CMD + l = add live song to setlist (and song pool, if it isn't there already)
CMD + o = add live song to setlist
CMD + e = toggle edit mode (yellow border in monitor area) 
SPACE = toggle scroll
SHIFT = hold to scroll
ESC = when talent window is in focus, toggle fullscreen
"<," / ".>" keys = page a few lines up or down

For now you can essentially save 1 setlist and 1 "pool" of imported songs.
These persist between runs of the program. You also have a folder to dump
rtf/txt versions of your song files (app/data/text_files) where they can be
quickly loaded and formatted. There is an SQLite database in play which can
hold imported song data but it has a long way to go before I would trust it
with a library. Basically, stick to the text_files folder for now!

Eventually there will be a robust data management system but I want to get
the fundamentals needed to survive a 2 hour gig first... Like custom
focus arrow colors, lol (implemented 3/30/22).

I am a touring professional teleprompter, hobbyist programmer, and I work
on this when I have time between gigs. Eventually hoping to code professionally,
hire me!

- Joel

P.S. Use this at your own risk. I take no responsibility for anything that
happens from use of this software, unless its good!
