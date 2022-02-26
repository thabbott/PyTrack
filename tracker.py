import skvideo.io
from skimage import measure
import numpy as np
from collections import deque

class Tracker():

    def __init__(self, fname):
        """ Initialize particle tracker.

        Arguments:
        fname -- path and name of video file
        """

        # Read entire video file and metadata into memory
        print('Reading video file')
        self.frames = skvideo.io.vread(fname)
        meta = skvideo.io.ffprobe(fname)
        print('Finished reading video file')

        # Set default parameters
        # Threshold lightness for separating dots from background
        self.threshold = 100
        # Control whether dots are darker than background
        self.dots_are_darker = True
        # Control whether tracking is active
        self.track = False
        # Step between frames
        self.dframe = 1
        # Video FPS
        self.fps = eval(meta['video']['@avg_frame_rate'])
        print(self.fps)

        # Set index of current frame
        self.iframe = 0

        # Initialize stacks for holding track information
        self.trackx = deque()
        self.tracky = deque()
        self.trackt = deque()
        self.tracki = deque()

        # Initialize coordinates of candidate point
        self.tx = np.nan
        self.ty = np.nan

    def reset(self):
        """ Reset tracker without re-reading video file. """
        self.iframe = 0
        self.trackx = deque()
        self.tracky = deque()
        self.trackt = deque()
        self.tracki = deque()
        self.tx = np.nan
        self.ty = np.nan

    def process_frame(self):
        """ Process current frame. """

        print('Processing frame %d' % self.iframe)

        # Create binary mask
        self.frame = self.frames[self.iframe,:,:,:]
        lightness = np.mean(self.frame, axis = -1)
        if self.dots_are_darker:
            self.binary = (lightness < self.threshold)
        else:
            self.binary = (lightness > self.threshold)

        # Assign labels to connected components
        labels = measure.label(self.binary, background = 0)

        # Calculate properties of labeled regions
        regions = measure.regionprops(labels)

        # Add centroids to candidate list
        self.cx = np.array([region.centroid[1] for region in regions])
        self.cy = np.array([region.centroid[0] for region in regions])

        print('Finished processing frame %d' % self.iframe)

    def track_at(self, x, y):
        """ Identify candidate centroid closest to input coordinates.

        Arguments:
        x -- approximate x coordinate of object
        y -- approximate y coordinate of object
        """

        # Calculate distances from input coordinates to centroids
        dist = np.sqrt((self.cx - x)**2 + (self.cy - y)**2)

        # Find index of minimum-distance centroid
        ind = np.argmin(dist)

        # Save location of centroid
        self.tx = self.cx[ind]
        self.ty = self.cy[ind]

    def advance(self):
        """ Add current candidate to track and advance frame. """

        # Add points to track provided tracking is active,
        # frame is not already at the end of the stored track
        # (which can happen at the end of the video file),
        # and a candidate point has been identified.
        if (self.track
            and (len(self.tracki) == 0 or self.tracki[-1] < self.iframe)
            and not np.isnan(self.tx)):
            self.trackx.append(self.tx)
            self.tracky.append(self.ty)
            self.tracki.append(self.iframe)
            self.trackt.append(self.iframe/self.fps)

        # Increment frame counter and check bounds
        self.iframe += self.dframe
        self.iframe = min(self.iframe, self.frames.shape[0] - 1)

    def rewind(self):
        """ Rewind track. """

        # Decrement frame counter and check bounds
        self.iframe -= self.dframe
        self.iframe = max(self.iframe, 0)

        # Pop elements past frame counter from track
        while len(self.tracki) > 0 and self.tracki[-1] >= self.iframe:
            self.trackx.pop()
            self.tracky.pop()
            self.trackt.pop()
            self.tracki.pop()

    def update(self):
        """ Update tracker after changing frame or parameters """

        self.process_frame()
        if self.track and len(self.trackx) > 0:
            self.track_at(self.trackx[-1], self.tracky[-1])
        else:
            self.tx = np.nan
            self.ty = np.nan

    def save(self, fname):
        """ Save track to text file """
        with open(fname, 'w') as f:
            f.write('\n')
            f.write('$NEW TRACK\n')
            f.write('HR\t MIN\t SEC\t MSEC\t X(px)\t Y(px)\n')
            for x, y, t in zip(self.trackx, self.tracky, self.trackt):
                tmsec = int(t*1000)
                msec = tmsec % 1000
                sec = tmsec//1000 % 60
                mins = tmsec//(1000*60) % 60
                hr = tmsec//(1000*60*60)
                f.write('%d\t %d\t %d\t %04d\t %04d\t %04d\n' %
                    (hr, mins, sec, msec, x, y))
            f.write('$$END TRACK')
