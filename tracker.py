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

        self.reset()

    def reset(self):
        """ Reset tracker without re-reading video file. """
        
        # Set index of current frame
        self.iframe = 0
        
        # Initialize stacks for holding track information
        self.trackx = [] # deque()
        self.tracky = [] # deque()
        self.trackt = [] # deque()
        self.tracki = [] # deque()
        
        # Initialize coordinates of candidate point
        self.tx = [] # np.nan
        self.ty = [] # np.nan
    
    def num_frames(self):
        """ Return total number of frames in video """
        return self.frames.shape[0]

    def first_track(self):
        """ Return index of first track """
        return 0

    def last_track(self):
        """ Return index of last track """
        return len(self.trackx) - 1

    def num_tracks(self):
        """ Return number of tracks """
        return len(self.trackx)

    def track_indices(self):
        """ Return iterator with indices of all tracks """
        return range(self.first_track(), self.last_track() + 1)

    def add_track(self):
        """ Add a new track to the tracker """
        self.trackx.append(deque())
        self.tracky.append(deque())
        self.trackt.append(deque())
        self.tracki.append(deque())
        self.tx.append(np.nan)
        self.ty.append(np.nan)

    def remove_track(self, ind):
        """ Remove a track from the tracker 

        Arguments:
        ind: index of the track to be removed
        """

        if ind == None:
            return
        
        self.trackx.pop(ind)
        self.tracky.pop(ind)
        self.trackt.pop(ind)
        self.tracki.pop(ind)
        self.tx.pop(ind)
        self.ty.pop(ind)

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

    def track_at(self, active_track, x, y):
        """ Identify candidate centroid closest to input coordinates.

        Arguments:
        active_track -- index of track to which candidate centroid is assigned
        x -- approximate x coordinate of object
        y -- approximate y coordinate of object
        """

        if active_track == None:
            return

        # Calculate distances from input coordinates to centroids
        dist = np.sqrt((self.cx - x)**2 + (self.cy - y)**2)

        # Find index of minimum-distance centroid
        ind = np.argmin(dist)

        # Save location of centroid
        self.tx[active_track] = self.cx[ind]
        self.ty[active_track] = self.cy[ind]

    def advance(self):
        """ Add current candidate to track and advance frame. """

        # Add points to track provided tracking is active,
        # frame is not already at the end of the stored track
        # (which can happen at the end of the video file),
        # and a candidate point has been identified.
        for active_track in self.track_indices():
            if (self.track
                and (
                    len(self.tracki[active_track]) == 0 or 
                    self.tracki[active_track][-1] < self.iframe
                )
                and not np.isnan(self.tx[active_track])):
                self.trackx[active_track].append(self.tx[active_track])
                self.tracky[active_track].append(self.ty[active_track])
                self.tracki[active_track].append(self.iframe)
                self.trackt[active_track].append(self.iframe/self.fps)

        # Increment frame counter and check bounds
        self.iframe += self.dframe
        self.iframe = min(self.iframe, self.frames.shape[0] - 1)

    def rewind(self):
        """ Rewind track. """

        # Decrement frame counter and check bounds
        self.iframe -= self.dframe
        self.iframe = max(self.iframe, 0)

        # Pop elements past frame counter from track
        for active_track in self.track_indices():
            while (
                    len(self.tracki[active_track]) > 0 and 
                    self.tracki[active_track][-1] >= self.iframe
            ):
                self.trackx[active_track].pop()
                self.tracky[active_track].pop()
                self.trackt[active_track].pop()
                self.tracki[active_track].pop()

    def update(self):
        """ Update tracker after changing frame or parameters """

        self.process_frame()
        for active_track in self.track_indices():
            if self.track and len(self.trackx[active_track]) > 0:
                self.track_at(
                        active_track,
                        self.trackx[active_track][-1], 
                        self.tracky[active_track][-1]
                )
            else:
                self.tx[active_track] = np.nan
                self.ty[active_track] = np.nan

    def save(self, fname):
        """ Save track to text file """
        with open(fname, 'w') as f:
            for active_track in self.track_indices():
                f.write('\n')
                f.write('$NEW TRACK\n')
                f.write('HR\t MIN\t SEC\t MSEC\t X(px)\t Y(px)\n')
                for x, y, t in zip(
                        self.trackx[active_track], 
                        self.tracky[active_track], 
                        self.trackt[active_track]):
                    tmsec = int(t*1000)
                    msec = tmsec % 1000
                    sec = tmsec//1000 % 60
                    mins = tmsec//(1000*60) % 60
                    hr = tmsec//(1000*60*60)
                    f.write('%d\t %d\t %d\t %04d\t %04d\t %04d\n' %
                        (hr, mins, sec, msec, x, y))
                f.write('$$END TRACK')
