from JPEG import JPEG
import numpy as np
from PIL import Image
import scipy.io
filename = "bw.jpg"
#filename = "out.jpg"
a = JPEG(filename)
a.encode("out.jpg")

exit()
a.decode()
imdata = a.Image
img = Image.fromarray(imdata,'L')
img.show()
#scipy.io.savemat('test.mat', dict(imdata=a.Image
a.QUANT_TABLE.printBlock()
a.HUFF_TABLE.printBlock()
a.SOF0.printBlock()
a.SOSHEADER.printBlock()
