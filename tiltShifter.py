import sys
import struct
from PIL import Image
from scipy import ndimage
import numpy as nump
import PIL.ImageOps
import matplotlib.pyplot as plt

def main():
	colorImage = Image.open("photo_crop.jpg")
	with open("distance_crop.pfm", "rb") as f:
		mask = produceGrayscaleFromPfm(f)
	blurredBase = gauss(colorImage)
	makeTiltShift(colorImage, blurredBase, mask, 90, 50, 1, 10, 255)


def makeTiltShift(colorImage, blurredBase,  mask, angle=90, offsetInit=50, offsetStart=18, offsetEnd=10, focus=10):
	#mask = PIL.ImageOps.invert(mask)
	pixelMap = mask.load()
	newImg = Image.new(mask.mode, mask.size)
	pixelsNew = newImg.load()

	for i in range(newImg.size[0]): # width
		for j in range(newImg.size[1]): # height
			if pixelMap[i,j] < offsetStart or pixelMap[i,j] > offsetEnd:
				pixelsNew[i,j] = focus
			else:
				pixelsNew[i,j] = pixelMap[i,j] # leave the original ones

	# apply blur to parametrized mask
	blurMask = gaussianFilter(newImg, 10)
	colorImage.paste(blurredBase, mask=blurMask)
	colorImage.save("1.jpg", "JPEG")
	mask.save("2.jpg", "JPEG")
	blurMask.save("blurMask.jpg", "JPEG")
	newImg.save("parametrizedMask.jpg", "JPEG")
	colorImage.show()

def gauss(image): # blur for color
	img = ndimage.gaussian_filter(image, sigma=(5,5,0), order=0)
	plt.imshow(img, interpolation='nearest')
	return(Image.fromarray(img))

def gaussianFilter(image, blurAmount=5): # blur for bw
	blurred = nump.array(image, dtype=float)
	blurred = ndimage.gaussian_filter(blurred, sigma=blurAmount)
	blurred = Image.fromarray(nump.uint8(blurred))
	return(blurred)

def produceGrayscaleFromPfm(f):
	header = sken(f)
	if header[1] == b'f':
		# black and white
		pass
	else:  # color not supported
		sys.exit(1)

	dimensions = sken(f)
	strDimensions = str(b''.join(dimensions), 'utf-8').split(' ')
	width = int(strDimensions[0])
	height = int(strDimensions[1])
	sken(f) # overhead data

	resultArr = []
	for y in range(0, height):
		for x in range(0, width):
			distanceData = f.read(4)
			resultArr.append(getFloat(distanceData))
	maxVal = max(resultArr)
	minVal = min(resultArr)

	imageArr = []
	for value in resultArr:
		imageArr.append(translate(value, minVal, maxVal, 0, 255))

	size = width, height
	im = Image.new('L', size)
	im.putdata(imageArr)
	im = im.transpose(Image.FLIP_TOP_BOTTOM)
	return(im)

def getFloat(data):
	a = struct.unpack('f', data)
	return(float(a[0]))

def sken(f):
	#read until new line
	arr = []
	while True:
		tmp = f.read(1)
		if (tmp == b'\n'):
			break
		arr.append(tmp)
	return arr

# translate image pixel range to another range (i.e. 0-255)
def translate(value, leftMin, leftMax, rightMin, rightMax):
	leftSpan = leftMax - leftMin
	rightSpan = rightMax - rightMin
	valueScaled = float(value - leftMin) / float(leftSpan)
	return rightMin + (valueScaled * rightSpan)

main()