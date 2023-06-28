# PyTrack

This branch is an update that reads frames lazily rather than loading videos into memory in their entirety. This updates depends on two additional packages, listed in `environment.yml`. To replace an existing pytrack environment with one that includes these packages, run
```
conda env create --force -n pytrack -f environment.yml
```
Or, choose a different environment name.

---

Particle tracking for fluids experiments. This code is new and relatively untested, so don't be shy about opening an issue if you try to use it and run into problems.

To create a conda environment for running PyTrack, run 
```
conda env create -n pytrack -f environment.yml
```
Make sure to use `environment.yml` and not `environment.txt`; the latter is not platform-independent.

An MP4 file for testing the particle tracker (used in [this demo](https://vimeo.com/682323089)) is available at https://drive.google.com/file/d/1G3cqyRJSC0-zR0z1_zTEUU8DXOLQbLro/view?usp=sharing.
