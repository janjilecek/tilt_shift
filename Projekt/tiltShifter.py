import struct
import sys

import PIL
import matplotlib.pyplot as plt
import numpy as nump
from PIL import Image
from PIL import ImageOps
from scipy import ndimage

import tiltshift

class TiltShift:
	def run(self):
		colorImage = Image.open(self.name)
		with open(self.measured, "rb") as f:
			mask = self.produceGrayscaleFromPfm(f)
		blurredBase = self.gauss(colorImage)
		self.makeTiltShift(colorImage, blurredBase, mask, 10)

	# makeTiltShift parameters:
	# blur: blur radius in pixels
	# direction: angle of the tilt (hard mask, ignores distance data)
	def makeTiltShift(self, colorImage, blurredBase,  mask, bluring=10):
		#mask = ImageOps.invert(mask)
		pixelMap = mask.load()
		newImg = Image.new(mask.mode, mask.size)
		pixelsNew = newImg.load()

		for i in range(newImg.size[0]): # width
			for j in range(newImg.size[1]): # height
				pixelsNew[i,j] = pixelMap[i,j] # copy by pixels
				#if cond.. else: pixelsNew[i,j] = 255; # all white, all blur

		# apply blur to parametrized mask
		blurMask = self.gaussianFilter(newImg, bluring)
		colorImage.paste(blurredBase, mask=blurMask)
		colorImage.save(self.output, "JPEG")
		mask.save("2.jpg", "JPEG")
		blurMask.save("blurMask.jpg", "JPEG")
		newImg.save("parametrizedMask.jpg", "JPEG")
		newImg.show()
		colorImage.show()

	def gauss(self, image): # blur for color
		img = ndimage.gaussian_filter(image, sigma=(5,5,0), order=0)
		plt.imshow(img, interpolation='nearest')
		return(Image.fromarray(img))

	def gaussianFilter(self, image, blurAmount=5): # blur for bw
		blurred = nump.array(image, dtype=float)
		blurred = ndimage.gaussian_filter(blurred, sigma=blurAmount)
		blurred = Image.fromarray(nump.uint8(blurred))
		return(blurred)

	def produceGrayscaleFromPfm(self, f):
		header = self.sken(f)
		if header[1] == b'f':
			# black and white
			pass
		else:  # color not supported
			sys.exit(1)

		dimensions = self.sken(f)
		strDimensions = str(b''.join(dimensions), 'utf-8').split(' ')
		width = int(strDimensions[0])
		height = int(strDimensions[1])
		self.sken(f) # overhead data

		resultArr = []
		for y in range(0, height):
			for x in range(0, width):
				distanceData = f.read(4)
				resultArr.append(self.getFloat(distanceData))
		maxVal = max(resultArr)
		minVal = min(resultArr)

		resultArr = self.simulateLens(resultArr, width, height, minVal, maxVal)

		imageArr = []
		for value in resultArr:
			imageArr.append(self.translate(value, minVal, maxVal, 0, 255))

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
	def simulateLens(self, arr, width, height, minVal, maxVal):
		print("minimal meters:" + str(minVal))
		print("maximal meters:" + str(maxVal))

		for x in range(0, width):
			for y in range(0, height):
				data = arr[y * width + x]
				if data > self.meterEnd or data < self.meterStart or data == -1: # the focus plane
					arr[y * width + x] = maxVal

		return(arr)

	def getFloat(self, data):
		a = struct.unpack('f', data)
		return(float(a[0]))

	def sken(self, f):
		#read until new line
		arr = []
		while True:
			tmp = f.read(1)
			if (tmp == b'\n'):
				break
			arr.append(tmp)
		return arr

	# translate image pixel range to another range (i.e. 0-255)
	def translate(self, value, leftMin, leftMax, rightMin, rightMax):
		leftSpan = leftMax - leftMin
		rightSpan = rightMax - rightMin
		valueScaled = float(value - leftMin) / float(leftSpan)
		return rightMin + (valueScaled * rightSpan)


	def __init__(self, coc, aperture, focus, tilt, distance, unit, name="photo_crop.jpg", measured="distance_crop.pfm", output="output.jpg"):
		#tiltshift.depthOfField(0.06,5.6,29,0.8,1.3,1.0)
		dof = tiltshift.depthOfField(coc, aperture, focus, tilt, distance, unit)
		met = tiltshift.calcMeters(dof[0], dof[1], dof[2])

		self.meterStart = met[0]
		self.meterEnd = met[1]

		self.name = name
		self.measured = measured
		self.output = output


def main():
	#ts = TiltShift(0.06,5.6,29,0.8,1.3,1.0)
	#ts = TiltShift(0.01,11,90,0.55,400.5,1.0)

	try:
		switch = sys.argv[1]
	except Exception:
		help()
		sys.exit(1)

	if (switch == "m"):
		try:
			ts = TiltShift(0.01,1,90,0.5,400,1)

			m1 = float(sys.argv[2])
			m2 = float(sys.argv[3])
			ts.meterStart = m1
			ts.meterEnd = m2
		except Exception as e:
			print("---------->" + str(e))
			help()
			sys.exit(1)
	elif (switch == "ts"):
		try:
			coc = float(sys.argv[2])
			aperture = float(sys.argv[3])
			focus = float(sys.argv[4])
			tilt = float(sys.argv[5])
			dist = float(sys.argv[6])

			ts = TiltShift(coc, aperture, focus, tilt, dist, 1.0)
		except Exception as e:
			print("--------->" + str(e))
			help()
			sys.exit(1)
	else:
		print("Enter valid parameters, please")
		help()
		sys.exit(1)

	ts.run()

def help():
	print("for hard meters range (i.e. from 200 to 500) use 'm' as first param, then start and end meters\n"
		  " ./tiltshift.py m 200 500 [nameOfFile.jpg] [distanceFile.pfm] [outputName.jpg]\n"
		  "default filenames: photo_crop.jpg, distance_crop.pfm, output.jpg")
	print("for true tilt shift use switch 'ts' and then:"
		  "circle of confusion: in mm (0.01)\n"
		  "aperture number: 2.8\n"
		  "focal length mm: in mm (90)\n"
		  "tilt in degrees: 45\n"
		  "distance of normal focus: in meters (400)\n"
		  "so for example:\n"
		  "python .\\tiltShifter.py ts 0.01 1 90 0.55 400 nameOfFile.jpg distanceFile.pfm outputName.jpg\n"
		  "that will produce focus from 316 to 1346 meters (88 angle1, 89,6 angle2, scheimpflug point 9.4 m under camera")
main()