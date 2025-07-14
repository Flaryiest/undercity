Do you like Squid Game!!!

<img width="2547" height="3296" alt="Sample Assembly" src="https://github.com/user-attachments/assets/c4352ae9-fcac-4a8e-960c-9ef75fe71828" />
This project is a flywheel disc shooter mounted on a turret platform with motion detection, simulating the "Red Light, Green Light" game in Squid Game.

We made a few unique design choices while CADing and programming the launcher.
- To sustain a semi-automatic speed, we used a gravity-fed hopper design, in which the discs slowly fall into the barrel.
  <img width="981" height="780" alt="image" src="https://github.com/user-attachments/assets/aa34ea3c-ff2f-4cc5-8582-b6ad0510579e" />

- To create linear motion for pushing the discs into the flywheel, we used a rack and pinion setup where the back wall had a rack under it and was geared to a servo below:

  <img width="662" height="626" alt="image" src="https://github.com/user-attachments/assets/a31e4380-c4ca-4f95-97a2-0022b4499a14" />

- To combat the load of the battery and motor on the turret platform, we geared the stepper motor in a 1:2 ratio:
  <img width="376" height="499" alt="image" src="https://github.com/user-attachments/assets/bbcd4e63-0474-450b-8b08-2f005c5d5bd7" />



Unfortunately, the turret platform did not print in time, and our robot cannot turn around, so we decided to scale down the project and focus on the launcher mechanism.

If there is motion directly in front of the launcher, the launcher fires, sort of like a sentry watching a set sightline.

## Firmware  
The code is done on a combination of a orpheus pico and a computer. The computer does the motion detection and depth tracking in motionDetection.py, using opencv and MiDaS. From there, it sends commands to the pico which then runs the motor and servo.  
The orpheus pico and electronics use circuit python, and relies on the adafruit motor library.  
motion detection:  https://www.youtube.com/shorts/whcpX-JFEPc


## Bill of Materials (BOM)

| Quantity | Item | Link |
|----------|------|------|
| 14 | 3D Printed Parts | (Lots of filament) |
| 1 | Webcam | [FWV Streaming Webcam](https://www.amazon.com/FWV-Streaming-Microphone-Desktop-Studying/dp/B0D72VQR6Q?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&psc=1&smid=A36LVV2HAP7FK3&gQT=1) |
| 1 | 550 Motor | [REV Robotics 550 Motor](https://www.revrobotics.com/rev-21-1651/?gQT=2) |
| 1 | 7.4V 2S Battery | [Zeee 7.4V Battery](https://www.amazon.com/Zeee-Batteries-Dean-Style-Connector-Vehicles/dp/B076Z778MJ?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&psc=1&smid=A646DVGSXYMNH&gPromoCode=cpn_us_en_pct_20_2025Q2&gQT=1) |
| 1 | Stepper Motor | [STEPPERONLINE Bipolar Stepper](https://www.amazon.com/STEPPERONLINE-Stepper-Bipolar-Connector-compatible/dp/B00PNEQKC0?dib=eyJ2IjoiMSJ9.hN-9QQUUabt-Xybqh_2heZErnxbgksLDP0FLL9IfB20DcgL3MP0jscRJUTv3cKjK_EhHKm97OEFgr9w4Yimkca5c6nsy7kl77bFJ0cz3XpUv5DdZEGwHgObEWgdkugO36gM4hi_hqj6v7HwdwNKyh4brTdtUYrr-8qQTI39tWqkEC7tWdxDZwm5f06zhnHQ7hRKYNt85A6cCEqcz8Yd14esjjfUFoUWLnj-D9eyl4So.v7ZlBBTxBiePDv4_OvINUIP3Of8ztWi0Z0JxgSpzMVA&dib_tag=se&keywords=Stepper+Motor&qid=1752500433&sr=8-3) |
| 1 | Stepper Motor Driver (A4988) | [Pololu A4988 Driver](https://www.pololu.com/product/1182) |
| 1 | Small Servo | [Micro Servo](https://www.amazon.com/Micro-Servos-Helicopter-Airplane-Controls/dp/B07MLR1498?dib=eyJ2IjoiMSJ9.POZxW8ictf28-1c0EFTfUjj_MoyYfzzsuC5MMwjT6raJJmiC2l4tbAhq2I6OQuTtXZ5jeyqRZtU24PFEkESl_AZgy1pOiXi1LMLC3YVKq-8920EopDx5Xh_Grr-Q7Qip7xw6Qb-n9roBfzVwd-hcmwfrjXN9axHXlOrt3ED6ptTK9uN4Lq1oTjIygM7WV5OZLeCt_ngN8xdoUho2dhz_E0ovX9usQ-dEE8GjMABkFX7h0a7QkCNbW133R_x06JglnTpVSHmRTDt6HjORXDFuyeAHP6hErDHiZP4kcANhM3Q.rrCXlX-dEgNtKnkm_FFS6nNXc9-RH3TAgRwpZ6ptrMc&dib_tag=se&keywords=servos&qid=1752500480&sr=8-6) |
| 1 | Orpheus Pico | [Raspberry Pi Pico](https://www.microcenter.com/product/661033/raspberry-pi-pico-microcontroller-development-board?rd=1) |
| 1 | Breadboard | [400-point Breadboard](https://www.amazon.com/BB400-Solderless-Plug-BreadBoard-tie-points/dp/B0040Z1ERO?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&psc=1&smid=A2RKGEIGG4B1JT&gQT=1) |

