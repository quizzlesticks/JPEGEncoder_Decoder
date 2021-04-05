from JPEG import JPEG
filename = "PicGrayscale.jpg"
a = JPEG(filename)
a.decode()
a.QUANT_TABLE.printBlock()
#a.HUFF_TABLE.printBlock()
#a.HUFF_TABLE.printBlock()
#a.SOF0.printBlock()
#a.SOSHEADER.printBlock()
