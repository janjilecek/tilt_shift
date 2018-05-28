import math

def depthOfField(coc, aperture, focal, tilt, distance, distance_unit):
	if (focal <= 0 ):
		raise ValueError('Please enter a positive numerical value for the focal length in mm.')
	else:
		if (tilt < 0.5 ):
			raise ValueError('Please enter a numerical value of at least 0.5 degrees for the lens tilt.')
		else:
			if ( distance < 0.3 ):
				raise ValueError('Please enter a numerical value of at least 0.3 meters for the focusing distance.')
			else:
				distanceInMm = 1000*distance/distance_unit # converts distance to mm's
				tilt = (math.pi/180) * tilt # converts tilt from degrees into radians
				jValue = 0.001 * focal / math.sin( tilt ) # in meters
				A = focal / ( 1-focal/distanceInMm ) # this value is very susceptible to errors caused by the thin lens approximation

				phi = (180/math.pi) * math.atan( math.sin(tilt) / ( math.cos(tilt) - focal/A ) ); # angle of focal plane relative to unshifted position, in direction of tilt
				if ( phi < 0 ): phi = 180 + phi # if focal plane is rotated past ninety degrees
				jvalValue = round(10 * jValue) / 10

				# calculated near and far planes of acceptable sharpness
				stemp = focal / ( coc * aperture )
				dNear = A / (stemp-1) # near depth of focus
				dFar = A / (stemp+1) # far depth of focus

				nearDoFAngle = (180/math.pi) * math.atan( math.sin(tilt) / ( math.cos(tilt) - focal/(A+dNear) ) )# near depth of field angle in degrees
				farDoFAngle = (180/math.pi) * math.atan( math.sin(tilt) / ( math.cos(tilt) - focal/(A-dFar) ) ) # far depth of field angle in degrees
				if farDoFAngle < 0 : farDoFAngle = 180 + farDoFAngle
				if nearDoFAngle < 0: nearDoFAngle = 180 + nearDoFAngle

				dNear = round(10 * nearDoFAngle) / 10
				dFar = round(10 * farDoFAngle) / 10

				print(dNear)
				print(dFar)
				print(jvalValue)
				return(dNear, dFar, jvalValue)

def tiltShift(focal, shiftAmount):
	if (focal <= 0 ):
		raise ValueError('Please enter a positive numerical value for the focal length.')
	else:
		if (shiftAmount <= 0):
			raise ValueError('Please enter a positive numerical value for the shift amount.')
		else:
			angle = (180/math.pi) * math.atan(shiftAmount / focal) # long dimension angle of view in degrees
			fPlaneRotation = round(10 * angle) / 10
			print(fPlaneRotation)

def calcMeters(angle1, angle2, jVal):
	metersStart = jVal * math.tan(math.radians(angle1))
	metersEnd = jVal * math.tan(math.radians(angle2))

	print("-meters-")
	print(metersStart)
	print(metersEnd)
	return (metersStart, metersEnd)

# coc, f, mm, angle, meters, unit
#dof = depthOfField(0.06,5.6,29,0.8,1.3,1.0)
#print("---")
#calcMeters(dof[0],dof[1],dof[2])