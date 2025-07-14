Do you like Squid Game!!!

<img width="2547" height="3296" alt="Sample Assembly" src="https://github.com/user-attachments/assets/c4352ae9-fcac-4a8e-960c-9ef75fe71828" />
This project is a flywheel disc shooter mounted on a turret platform with motion detection, simulating the "Red Light, Green Light" game in Squid Game.

We made a few unique design choices while CADing and programming the launcher.
- To sustain a semi-automatic speed, we used a gravity-fed hopper design, in which the discs slowly fall into the barrel.
- To create linear motion for pushing the discs into the flywheel, we used a rack and pinion setup where the back wall had a rack under it and was geared to a servo below.
- To combat the load of the battery and motor on the turret platform, we geared the stepper motor 1:2.

Unfortunately, the turret platform did not print in time, and our robot cannot turn around, so we decided to scale down the project and focus on the launcher mechanism.

If there is motion directly in front of the launcher, the launcher fires, sort of like a sentry watching a set sightline.
