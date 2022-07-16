#!/usr/bin/env python3

import math
import sys
import unittest
from test_tools_box import Colors
from texttable import Texttable
import logging

import logger as lg
logger = lg.mylogger(__name__)

class ScaraArm:
	STRAIGHT_ANGLE = 180
	MINIMAL_X_COORDINATE = 0.0001

	def __init__(self, arm_r1 = 0, arm_r2 = 0):
		self.length_of_arm1 = arm_r1
		self.length_of_arm2 = arm_r2
		self.current_angle_r1 = 0
		self.current_angle_r2 = 0
		self.current_x = None
		self.current_y = None
		logger.info("Scara arm initieted. Larm1:{} Larm2:{} Angle1:{} Angle2:{} currentX:{} currentY:{}".\
					format(self.length_of_arm1, \
					self.length_of_arm2, \
					self.current_angle_r1, \
					self.current_angle_r2, \
					self.current_x, \
					self.current_x))

	def _calc_arm1_angle(self, x = 0.0, y = 0.0):
		self.arm_angle = (self.STRAIGHT_ANGLE / math.pi) * \
				(math.atan(float(y / x)) - \
				math.acos(( x**2 + y**2 + (self.length_of_arm1**2) - (self.length_of_arm2**2)) / \
				((2 * self.length_of_arm1) * math.sqrt(x**2 + y**2))))

		return int(self.arm_angle)

	def _calc_arm2_angle(self, x = 0.0, y = 0.0):
		self.arm_angle = (self.STRAIGHT_ANGLE / math.pi) * \
				(math.acos((x**2 + y**2 - self.length_of_arm1**2 - self.length_of_arm2**2) / \
				(2 * self.length_of_arm1 * self.length_of_arm2)))

		return int(self.arm_angle)

	def calc_scara_angles_middle(self, x, y, init_x = 0, init_y = 0):
		mx = self.current_x
		my = self.current_y

		if mx == None or my == None:
			mx = init_x
			my = init_y

		mx = int((x + mx)/2)
		my = int((y + my)/2)
		return self.calc_scara_angles(mx, my)

	def calc_scara_angles(self, x, y):
		self.new_angle_r1 = 0
		self.new_angle_r2 = 0
		self.previous_angle_r1 = 0
		self.previous_angle_r2 = 0

		try:
			if self.current_x == x and self.current_y == y:
				logger.debug("X and Y unchanged")
				return (0, 0)

			if 0 == x and 0 == y:
				self.new_angle_r1 = 0
				self.new_angle_r2 = self.STRAIGHT_ANGLE
				logger.debug("A and Y seto to 0, 0")
			else:
				if 0 == x:
					x = self.MINIMAL_X_COORDINATE

				if x < 0:
					self.new_angle_r1 = self.STRAIGHT_ANGLE

				self.new_angle_r1 += self._calc_arm1_angle(x, y)
				self.new_angle_r2 += self._calc_arm2_angle(x, y)
				#commented out due to huge time consumption
				#logger.debug("X and Y set to {}, {}. New angles A1, A2 {}, {}".\
				#			format(x,y,self.new_angle_r1,self.new_angle_r2))

			self.previous_angle_r1 = self.current_angle_r1
			self.previous_angle_r2 = self.current_angle_r2
			self.current_angle_r1 = self.new_angle_r1
			self.current_angle_r2 = self.new_angle_r2
			self.current_x = x
			self.current_y = y

			return (self.new_angle_r1 - self.previous_angle_r1, self.new_angle_r2 - self.previous_angle_r2)
		except:
			logger.warning("Cannot determine angles for x:{} y:{}".format(x, y))
			return (None, None)
		
	def translate_scara_to_sm(self, sm_steps_per_resolution, out_from_calc_scara_angles1, out_from_calc_scara_angles2=(None, None)):
		'''
		Metoda pobiera parametry:
		1 ilosc krokow na 1 obrot ramienia dla danego silnika krokowego
		  (liczona z uwzglednieniem zastosowanych przekladni)
		2 katy z wyniku dzialania metody calc_scara_angles
		
		nastepnie dokonuje przeksztalcen w celu uzyskania dla kazdego silnika
		krokowego 2 pary parametrow potrzebnych na jego wysterowanie 
		z wykozystaniem sterownika A4988 lub podobnego:
		1 kierunek obrotow
		2 ilosc krokow do wykonania w celu przesuniecia o zadany kat      
		
				 MOTOR ARM2             
				 DIRECTION21            
			     +-+ DIRECTION22            
			     +-+                        
			    /   \                       
			   /     \                      
			  /       \            --       
		   ARM1  /         \ARM2                
			/           \                   
		       /             \                  
		      /               \                 
		     /                 \                
		  +-+                   -               
		  +-+MOTOR ARM1                         
		     DIRECTION11                        
		     DIRECTION12                        		
		'''
		direction11, direction12, direction21, direction22 = 0, 0, 0, 0
		angle11, angle12 = out_from_calc_scara_angles1
		angle21, angle22 = out_from_calc_scara_angles2
		single_step = float(360/sm_steps_per_resolution)
	
		if angle11 == None:
			angle11 = 0
		elif angle11 < 0:
			direction11 = 1

		if angle12 == None:
			angle12 = 0
		elif angle12 < 0:
			direction12 = 1


		if angle21 == None:
			angle21 = 0
		elif angle21 < 0:
			direction21 = 1
			
		if angle22 == None:
			angle22 = 0
		elif angle22 < 0:
			direction22 = 1

		return (direction11, int(abs(angle11) / single_step), \
			direction12, int(abs(angle12) / single_step), \
			direction21, int(abs(angle21) / single_step), \
			direction22, int(abs(angle22) / single_step))

class ScaraArmTest(unittest.TestCase):
	def setUp(self):
		print(Colors.BLUE +"\nTEST CASE: {}".format(self._testMethodName) + Colors.END)
		self.error_list = []
		self.tc_count = 0

	def tearDown(self):
		print(100*"-")
		self.assertEqual([], self.error_list)

	def test_scara_accurancy(self):
		'''
		Scenario: x,y coordinates of start and stop position of the SCARA arm
		are the same. Calculate angles for all positions inside square 70/70
		for arm lengrh 50/50, with accurancy of 1.
		Verify: at the end sum of angles is equal to 0.
		'''
		R1 = 25
		R2 = 25
		max_xy = int(math.sqrt((2*R1)**2//2))
		print(max_xy)
		self.sa = ScaraArm(R1,R2)
		counter_a1 = 0
		counter_a2 = 0
		counter_possible_points = 0

		aR1,aR2 = self.sa.calc_scara_angles(R1+R2,0)
		counter_a1 += aR1
		counter_a2 += aR2
		for x in range(-max_xy,max_xy):
			for y in range(-max_xy,max_xy):
					aR1,aR2 = self.sa.calc_scara_angles(x,y)
					if aR1 == None:
						aR1 = 0
					if aR2 == None:
						aR2 = 0
					counter_a1 += aR1
					counter_a2 += aR2
					counter_possible_points += 1
		aR1,aR2 = self.sa.calc_scara_angles(R1+R2,0)
		counter_a1 += aR1
		counter_a2 += aR2
		try:
			status = self.assertEqual((0,0),(counter_a1, counter_a2))
		except AssertionError as e:
			status = e
			self.error_list.append(str(e))
		finally:
			if status == None:
				color = Colors.OKGREEN
			else:
				color = Colors.FAIL
			print(color + "Expected angle sum a1: {}\t a2:    {}\t Actual angle sum a1:    {}\t a2:    {}"\
				.format(0,0,counter_a1,counter_a2) + Colors.END)
			print("All possible positions for arms R1 {} R2 {}: {}".format(R1, R2, counter_possible_points))

	def test_scara_expected_positions(self):
		'''
		Scenario: calculate SCARA angles for known x,y,r1,r2 and expected angles.
		Verify: all expected values are equal to these calculated.
		'''
		self.sa = ScaraArm(5,5)

		for x, y, a1, a2 in [\
					(10,0,0,0),\
					(5,5,0,90),\
					(5,5,0,0),\
					(-5,5,90,0),\
					(-5,-5,90,0),\
					(5,-5,-270,0),\
					(5,-5,0,0),\
					(5,5,90,0),\
					(-5,-5,180,0),\
					(10,0,-180,-90),\
					(-10,0,180,0),\
					(-10,10,None,None),\
					(10,10,None,None),\
					(0,0,-180,180)\
					]:
			try:
				aR1,aR2 = self.sa.calc_scara_angles(x,y)
				status = self.assertEqual((a1,a2), (aR1,aR2))
			except AssertionError as e:
				status = e
				self.error_list.append(str(e))
			finally:
				if status == None:
					color = Colors.OKGREEN
				else:
					color = Colors.FAIL
				self.tc_count += 1
				print(color + "no {}\tx: {}\ty: {}\tExpected a1:    {}\t a2:    {}\t Actual a1:    {}\t a2:    {}"\
					.format(self.tc_count,x,y,a1,a2,aR1,aR2) + Colors.END)

		for item in self.error_list:
			print(item)
		self.assertEqual([], self.error_list)

def main():
	unittest.main()

if __name__ == "__main__":
	main()
