from PIL import Image, ImageDraw

img = Image.new('RGB', (900, 500), 'white')
d = ImageDraw.Draw(img)
lines = [
    'CENTRAL BOARD OF SECONDARY EXAMINATION',
    'STATEMENT OF MARKS',
    'Name: Rohan Sharma',
    'Father Name: Suresh Sharma',
    'Roll No: 1234567',
    'Registration No: CBSE2023998877',
    'Date of Birth: 12/05/2006',
    'Date of Issue: 30/06/2023',
    'Marks Obtained: 456',
    'Total Marks: 500',
]
y = 20
for line in lines:
    d.text((20, y), line, fill='black')
    y += 40
img.save('result_card.png')
