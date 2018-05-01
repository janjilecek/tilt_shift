import struct
import sys

import PIL
import matplotlib.pyplot as plt
import numpy as nump
from PIL import Image
from PIL import ImageOps
from scipy import ndimage


def main():
	colorImage = Image.open("photo_crop.jpg")
	with open("distance_crop.pfm", "rb") as f:
		mask = produceGrayscaleFromPfm(f)
	blurredBase = gauss(colorImage)
	makeTiltShift(colorImage, blurredBase, mask, 10, 90, 50, 1, 10, 255)

# makeTiltShift parameters:
# blur: blur radius in pixels
# direction: angle of the tilt (hard mask, ignores distance data)
def makeTiltShift(colorImage, blurredBase,  mask, bluring=10, angle=90, offsetInit=50, offsetStart=18, offsetEnd=10, focus=10):
	#mask = ImageOps.invert(mask)
	if (len(sys.argv) > 3): bluring = int(sys.argv[3]); # we take the argument if its provided
	pixelMap = mask.load()
	newImg = Image.new(mask.mode, mask.size)
	pixelsNew = newImg.load()

	for i in range(newImg.size[0]): # width
		for j in range(newImg.size[1]): # height
			pixelsNew[i,j] = pixelMap[i,j] # copy by pixels
			#if cond.. else: pixelsNew[i,j] = 255; # all white, all blur

	# apply blur to parametrized mask
	blurMask = gaussianFilter(newImg, bluring)
	colorImage.paste(blurredBase, mask=blurMask)
	colorImage.save("1.jpg", "JPEG")
	mask.save("2.jpg", "JPEG")
	blurMask.save("blurMask.jpg", "JPEG")
	newImg.save("parametrizedMask.jpg", "JPEG")
	newImg.show();
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

	resultArr = simulateLens(resultArr, width, height, minVal, maxVal, int(sys.argv[1]), int(sys.argv[2]), 2)

	imageArr = []
	for value in resultArr:
		imageArr.append(translate(value, minVal, maxVal, 0, 255))

	size = width, height
	im = Image.new('L', size)
	im.putdata(imageArr)
	im = im.transpose(Image.FLIP_TOP_BOTTOM)
	return(im)

# simulateLens parameters:
# arr: input array
# width, height: w and h of the image data
# minVal: minimal value in meters in image
# maxVal: maximal value in meters in image
# position: defines the point of focus (0-100) 66 would be 2/3 way in
# focus: amount of area that ins in focus (0-100) 10 would mean 1/10 of image is sharp
# fallout: area between focus and complete blur (0-100) lower value = tighter fade
def simulateLens(arr, width, height, minVal, maxVal, position, focus, fallout):
	print("minimal meters:" + str(minVal))
	print("maximal meters:" + str(maxVal))

	wholeRange = abs(maxVal)-abs(minVal)

	focused = wholeRange/100*focus
	positioned = wholeRange/100*position
	fellout = wholeRange/100*fallout

	for x in range(0, width):
		for y in range(0, height):
			data = arr[y * width + x]
			if (data > (position + focus) or data < (position-focus) or data == -1): # TODO new
				arr[y * width + x] = maxVal

	return(arr)

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