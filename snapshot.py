import skimage.io
from skimage import measure
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons, Button, Slider
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
figsize = (12, 8)
# Figure DPI (ppi)
dpi = 100
# Padding around elements
pad = 0.01

# Generate name for output file
def gen_savename():
    letters = string.ascii_lowercase
    fname = '%s.txt' % (''.join([random.choice(letters) for i in range(5)]))
    while os.path.exists(fname):
        fname = '%s.txt' % (''.join([random.choice(letters) for i in range(5)]))
    return fname

class Snapshot():

    def __init__(self, fname):
        self.img = skimage.io.imread(fname)
        self.threshold = 100
        self.dots_are_darker = True

    def process(self):
        self.isel = []
        self.selx = []
        self.sely = []
        lightness = np.mean(self.img, axis = -1)
        if self.dots_are_darker:
            self.binary = (lightness < self.threshold)
        else:
            self.binary = (lightness > self.threshold)
        labels = measure.label(self.binary, background = 0)
        regions = measure.regionprops(labels)
        self.cx = np.array([region.centroid[1] for region in regions])
        self.cy = np.array([region.centroid[0] for region in regions])

    def push_at(self, x, y):
        dist = np.sqrt((self.cx - x)**2 + (self.cy - y)**2)
        ind = np.argmin(dist)
        if not ind in self.isel:
            self.isel.append(ind)
            self.selx.append(self.cx[ind])
            self.sely.append(self.cy[ind])

    def pop(self):
        if len(self.isel) > 0:
            self.isel.pop()
            self.selx.pop()
            self.sely.pop()

    def save(self, savename):
        with open(savename, 'w') as f:
            f.write('xp\typ\n')
            for cx, cy in zip(self.selx, self.sely):
                f.write('%d\t%d\n' % (cx, cy))

# Set random filename for output
savename = gen_savename()

# Load image
snap = Snapshot(fname)
snap.process()

# Set up GUI
fig = plt.figure(figsize = figsize, dpi = 100)

# Add area for displaying current frame and track
imax = plt.axes([pad,pad,1-2*pad,0.8-2*pad])
imax.tick_params(axis = 'both', which = 'both', bottom = False, top = False,
    labelbottom = False, right = False, left = False, labelleft = False)

# Plot current frame
im = imax.imshow(snap.img)
centroids = imax.plot([], [], 'x', color = 'white')[0]
sel = imax.plot([], [], '.', color = 'blue')[0]

# Display controls
cbax = plt.axes([0.12+pad,0.8+pad,0.2-2*pad,0.2-2*pad])
cblabels = ['Show binary', 'Show centroids', 'Show selected']
cbstatuses = [False, False, False]
cbut = CheckButtons(cbax, cblabels, cbstatuses)
def cbfunc(label):
    ind = cblabels.index(label)
    status = cbut.get_status()
    if ind == 0:
        show_binary = status[ind]
        if show_binary:
            im.set_data(snap.binary)
            im.set_cmap('Greys')
            im.set_clim([0, 1])
        else:
            im.set_data(snap.img)
    if ind == 1:
        show_centroids = status[ind]
        if show_centroids:
            centroids.set_data(snap.cx, snap.cy)
        else:
            centroids.set_data([], [])
    if ind == 2:
        show_track = status[ind]
        if show_track:
            sel.set_data(snap.selx, snap.sely)
        else:
            sel.set_data([], [])
    plt.draw()
cbut.on_clicked(cbfunc)

# Display update
def update():
    status = cbut.get_status()
    if status[0]:
        im.set_data(snap.binary)
    else:
        im.set_data(snap.img)
    if status[1]:
        centroids.set_data(snap.cx, snap.cy)
    if status[2]:
        sel.set_data(snap.selx, snap.sely)
    plt.draw()

# Tracking controls
trax = plt.axes([0.6+pad,0.8+pad,0.2-2*pad,0.2-2*pad])
trlabels = ['Dark dots', 'Reset on save']
trstatuses = [True, False]
trbut = CheckButtons(trax, trlabels, trstatuses)
reset = trstatuses[1]
def trfunc(label):
    global reset
    ind = trlabels.index(label)
    status = trbut.get_status()
    if ind == 0:
        snap.dots_are_darker = status[ind]
    if ind == 1:
        reset = status[ind]
    plt.draw()
trbut.on_clicked(trfunc)

# Centroid selection
def onclick(event):
    if event.inaxes == imax:
        x = event.xdata
        y = event.ydata
        snap.push_at(x, y)
        update()
cid = fig.canvas.mpl_connect('button_press_event', onclick)

# Reset button
resax = plt.axes([0.8+pad,0.933+pad,0.2-2*pad,0.06-pad])
resbut = Button(resax, 'Reset')
def resfunc(event):
    snap.process()
    update()
resbut.on_clicked(resfunc)

# Undo button
undoax = plt.axes([0.8+pad,0.867+pad,0.2-2*pad,0.06-pad])
undobut = Button(undoax, 'Undo (backspace)')
def undofunc(event):
    snap.pop()
    update()
undobut.on_clicked(undofunc)

# Save button
saveax = plt.axes([0.8+pad,0.8+pad,0.2-2*pad,0.06-pad])
savebut = Button(saveax, 'Save (%s)' % savename)
def savefunc(event):
    global snap
    global savename
    snap.save(savename)
    if reset:
        snap.process()
        update()
        savename = gen_savename()
        savebut.label.set_text('Save (%s)' % savename)
    plt.draw()
savebut.on_clicked(savefunc)

# Threshold control
thrax = plt.axes([0.38+pad,0.933+pad,0.2-2*pad,0.06-pad])
thrslider = Slider(thrax, 'Threshold', 0, 255, valinit = snap.threshold, valstep = 1)
def thrfunc(val):
    snap.threshold = int(val)
    plt.draw()
thrslider.on_changed(thrfunc)

# Add keyboard shortcuts
def onpress(event):
    if event.key == 'backspace':
        undofunc(event)
fig.canvas.mpl_connect('key_press_event', onpress)

plt.show()
