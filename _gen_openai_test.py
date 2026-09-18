from PIL import Image, ImageDraw

img = Image.new('RGB', (900, 550), 'white')
d = ImageDraw.Draw(img)
lines = [
    'FEDERAL BOARD OF INTERMEDIATE AND SECONDARY EDUCATION',
    'SECONDARY SCHOOL CERTIFICATE EXAMINATION',
    'Certified that NOOR FATIMA',
    'Son of WAQAR AHMED',
    'CNIC: 37405-1234567-1',
    'Father CNIC: 37405-7654321-3',
    'Roll No: 1527311',
    'Registration No: 2328220128',
    'Date of Birth: 18-04-2007',
    'Institute: ARMY PUBLIC SCHOOL AND COLLEGE',
    'Total Marks: 1100',
    'Obtained Marks: 984',
    'Dated: Feb 01, 2024',
]
y = 20
for line in lines:
    d.text((20, y), line, fill='black')
    y += 40
img.save('openai_test.png')
