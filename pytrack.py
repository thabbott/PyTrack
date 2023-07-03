import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons, Button, Slider, TextBox
import numpy as np
import string
import random
import os
import sys
from tracker import Tracker

if len(sys.argv) != 2:
    print('Usage: python pytrack.py <file>')
    print('<file>: path to mp4 recording')
    sys.exit()

# Path to video file
fname = sys.argv[1]
# Figure size (inches)
figsize = (15, 8)
# Figure DPI (ppi)
dpi = 100
# Padding around elements
pad = 0.01
# Column width
colwidth = 1/6

# Generate name for output file
def gen_savename():
    letters = string.ascii_lowercase
    fname = '%s.txt' % (''.join([random.choice(letters) for i in range(5)]))
    while os.path.exists(fname):
        fname = '%s.txt' % (''.join([random.choice(letters) for i in range(5)]))
    return fname

# Set random filename for output
savename = gen_savename()

# Initialize particle tracker
tracker = Tracker(fname)
tracker.process_frame()

# Start track
tracker.track_at(636, 465)

# Set up GUI
fig = plt.figure(figsize = figsize, dpi = 100)

# Add area for displaying current frame and track
imax = plt.axes([pad,pad,1-2*pad,0.8-2*pad])
imax.tick_params(axis = 'both', which = 'both', bottom = False, top = False,
    labelbottom = False, right = False, left = False, labelleft = False)

# Plot current frame
im = imax.imshow(tracker.frame)
centroids = imax.plot([], [], 'x', color = 'white')[0]
candidate = imax.plot([], [], 'x', color = 'red')[0]
track = imax.plot([], [], '.', color = 'blue')[0]

# Add information about current frame
info = plt.annotate(
    'Current frame:\n%d\n\nTotal frames:\n%d\n\nCurrent time:\n%d s' %
    (tracker.iframe+1, tracker.frames.shape[0], tracker.iframe/tracker.fps),
    xy = (pad, 1-pad), xycoords = 'figure fraction', va = 'top', ha = 'left')

# Display controls
cbax = plt.axes([colwidth/2+pad,0.8+pad,colwidth-2*pad,0.2-2*pad])
cblabels = ['Show binary', 'Show centroids', 'Show track']
cbstatuses = [False, False, False]
cbut = CheckButtons(cbax, cblabels, cbstatuses)
def cbfunc(label):
    ind = cblabels.index(label)
    status = cbut.get_status()
    if ind == 0:
        show_binary = status[ind]
        if show_binary:
            im.set_data(tracker.binary)
            im.set_cmap('Greys')
            im.set_clim([0, 1])
        else:
            im.set_data(tracker.frame)
    if ind == 1:
        show_centroids = status[ind]
        if show_centroids:
            centroids.set_data(tracker.cx, tracker.cy)
        else:
            centroids.set_data([], [])
    if ind == 2:
        show_track = status[ind]
        if show_track:
            track.set_data(tracker.trackx, tracker.tracky)
        else:
            track.set_data([], [])
    plt.draw()
cbut.on_clicked(cbfunc)

# Display update
def update():
    status = cbut.get_status()
    if status[0]:
        im.set_data(tracker.binary)
    else:
        im.set_data(tracker.frame)
    if status[1]:
        centroids.set_data(tracker.cx, tracker.cy)
    if status[2]:
        track.set_data(tracker.trackx, tracker.tracky)
    candidate.set_data(tracker.tx, tracker.ty)
    info.set_text(
        'Current frame:\n%d\n\nTotal frames:\n%d\n\nCurrent time:\n%d s' %
        (tracker.iframe+1, tracker.frames.shape[0], tracker.iframe/tracker.fps))
    plt.draw()

# Tracking controls
trax = plt.axes([3*colwidth+pad,0.8+pad,colwidth-2*pad,0.2-2*pad])
trlabels = ['Track', 'Dark dots', 'Reset on save']
trstatuses = [False, True, False]
trbut = CheckButtons(trax, trlabels, trstatuses)
reset = trstatuses[2]
def trfunc(label):
    global reset
    ind = trlabels.index(label)
    status = trbut.get_status()
    if ind == 0:
        tracker.track = status[ind]
        if tracker.track and np.isnan(tracker.tx) and len(tracker.trackx) > 0:
            tracker.track_at(tracker.trackx[-1], tracker.tracky[-1])
            candidate.set_data(tracker.tx, tracker.ty)
        if not tracker.track:
            candidate.set_data([], [])
            tracker.tx = np.nan
            tracker.ty = np.nan
    if ind == 1:
        tracker.dots_are_dark = status[ind]
    if ind == 2:
        reset = status[ind]
    plt.draw()
trbut.on_clicked(trfunc)

# Centroid selection
def onclick(event):
    if event.inaxes == imax:
        x = event.xdata
        y = event.ydata
        tracker.track_at(x, y)
        candidate.set_data(tracker.tx, tracker.ty)
        plt.draw()
cid = fig.canvas.mpl_connect('button_press_event', onclick)

# Advance button
advax = plt.axes([4*colwidth+pad,0.933+pad,colwidth-2*pad,0.06-pad])
advbut = Button(advax, 'Advance (enter)')
def advfunc(event):
    tracker.advance()
    tracker.update()
    update()
advbut.on_clicked(advfunc)

# Rewind button
rewax = plt.axes([4*colwidth+pad,0.867+pad,colwidth-2*pad,0.06-pad])
rewbut = Button(rewax, 'Rewind (shift+enter)')
def rewfunc(event):
    tracker.rewind()
    tracker.update()
    update()
rewbut.on_clicked(rewfunc)

# Play button
playax = plt.axes([4*colwidth+pad,0.8+pad,colwidth-2*pad,0.06-pad])
playlab = ['Run (spacebar)', 'Pause (spacebar)']
playstat = 0
playbut = Button(playax, playlab[playstat])
def playfunc(event):
    global playstat 
    if playstat == 0:
        playstat = 1 
    else:
        playstat = 0
    playbut.label.set_text(playlab[playstat])
    plt.draw()
playbut.on_clicked(playfunc)

# Goto-frame controls 
frameax = plt.axes([5.15*colwidth+pad,0.933+pad,0.85*colwidth-2*pad,0.06-pad])
framebox = TextBox(frameax, 'Frame', initial='')
gtax = plt.axes([5*colwidth+pad,0.867+pad,colwidth-2*pad,0.06-pad])
gtbut = Button(gtax, 'Jump to frame')
def gtfunc(event):
    try:
        frame = int(framebox.text)
        tracker.iframe = max(0, min(frame - 1, tracker.num_frames() - 1))
    except ValueError:
        print('Could not convert %s to frame number' % (framebox.text))
    tracker.update()
    update()
gtbut.on_clicked(gtfunc)

# Save button
saveax = plt.axes([5*colwidth+pad,0.8+pad,colwidth-2*pad,0.06-pad])
savebut = Button(saveax, 'Save (%s)' % savename)
def savefunc(event):
    global tracker
    global savename
    tracker.save(savename)
    if reset:
        tracker.reset()
        tracker.process_frame()
        update()
        savename = gen_savename()
        savebut.label.set_text('Save (%s)' % savename)
    plt.draw()
savebut.on_clicked(savefunc)

# Threshold control
thrax = plt.axes([1.85*colwidth+pad,0.933+pad,colwidth-2*pad,0.06-pad])
thrslider = Slider(thrax, 'Threshold', 0, 255, valinit = tracker.threshold, valstep = 1)
def thrfunc(val):
    tracker.threshold = int(val)
    plt.draw()
thrslider.on_changed(thrfunc)

# Frame increment control
dfrax = plt.axes([1.85*colwidth+pad,0.8+pad,colwidth-2*pad,0.06-pad])
dfrslider = Slider(dfrax, 'Step size', 1, 30, valinit = tracker.dframe, valstep = 1)
def dfrfunc(val):
    tracker.dframe = int(val)
    plt.draw()
dfrslider.on_changed(dfrfunc)

# Update button
updax = plt.axes([1.85*colwidth+pad,0.867+pad,colwidth-2*pad,0.06-pad])
updbut = Button(updax, 'Update')
def updfunc(event):
    tracker.update()
    update()
updbut.on_clicked(updfunc)

# Add keyboard shortcuts
def onpress(event):
    print(event.key)
    if event.key == 'enter':
        advfunc(event)
    if event.key == 'shift+enter':
        rewfunc(event)
    if event.key == ' ':
        playfunc(event)
fig.canvas.mpl_connect('key_press_event', onpress)

# Implement automatic advancing with timer-driven event 
def ontick():
    if playstat == 1:
        advfunc(None)
timer = fig.canvas.new_timer(interval=300)
timer.add_callback(ontick)
timer.start()

# Disable keyboard shortcuts when text box is active 


plt.show()
