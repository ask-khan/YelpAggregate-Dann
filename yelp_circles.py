import requests
import math
import pandas as pd
import numpy as np
from geopy.distance import distance
from web.models import ApiKeys
                    
class ComputeYelpCircles():
	def __init__(self, county_id, category, search_from):
		df=pd.read_json('county_circles.json')
		self.main_center, self.main_radius = df.loc[int(county_id)][['centers','radius']].values
		self.points = pd.read_json(f'point_data/{county_id}.json').geo_shape.values
		try:
			self.points = self.points.item()
		except:
			self.points = self.points.tolist()

		self.circles = []
		self.category = category
		if search_from is None:
			search_from = "restaurants"
		self.search_from = search_from

	def get_hex_corners(self, center, r):
		x = center[0] + np.array([r,r/2,-r/2,-r,-r/2,r/2,r])
		y = center[1] + np.array([0,r*math.sqrt(3)/2,r*math.sqrt(3)/2,0,-r*math.sqrt(3)/2,-r*math.sqrt(3)/2,0])
		return x,y

	def radius_lat2m(self, p1,p2):
		return round(distance(p1,p2).m)

	def onSegment(self, p, q, r): 
		if ( (q[0] <= max(p[0], r[0])) and (q[0] >= min(p[0], r[0])) and 
			   (q[1] <= max(p[1], r[1])) and (q[1] >= min(p[1], r[1]))): 
			return True
		return False
	  
	def orientation(self, p, q, r): 
		# to find the orientation of an ordered triplet (p,q,r) 
		# function returns the following values: 
		# 0 : Colinear points 
		# 1 : Clockwise points 
		# 2 : Counterclockwise 
		  
		val = (float(q[1] - p[1]) * (r[0] - q[0])) - (float(q[0] - p[0]) * (r[1] - q[1])) 
		if (val > 0): 
			return 1
		elif (val < 0):
			return 2
		else:
			return 0

	def doIntersect(self, p1,q1,p2,q2): 
		  
		o1 = self.orientation(p1, q1, p2) 
		o2 = self.orientation(p1, q1, q2) 
		o3 = self.orientation(p2, q2, p1) 
		o4 = self.orientation(p2, q2, q1) 
	  
		if ((o1 != o2) and (o3 != o4)): 
			return True

		if ((o1 == 0) and self.onSegment(p1, p2, q1)): 
			return True

		if ((o2 == 0) and self.onSegment(p1, q2, q1)): 
			return True
	  
		if ((o3 == 0) and self.onSegment(p2, p1, q2)): 
			return True
	  
		if ((o4 == 0) and self.onSegment(p2, q1, q2)): 
			return True
	  
		return False

	def circle_inside(self, c):
		total=0
		for i in range(len(self.points)):
			p1=self.points[i]
			p2=self.points[(i+1)%len(self.points)]
			p3=c[0]
			p4=[c[0][0]+2*self.main_radius,c[0][1]]
			total += self.doIntersect(p1,p2,p3,p4)
		return total%2

	def circle_intersecting(self, c):
		for point in self.points:
			if (point[0]-c[0][0])**2 + (point[1]-c[0][1])**2 <= c[1]*c[1]:
				return True
		return False
	
	def __search(self, params):
		s = requests.session()
		api_key = ''
		for keys in ApiKeys.select():
			api_key = keys.key
		s.headers = {
			"Authorization": "Bearer " + api_key
		}

		results = []
		r = s.get("https://api.yelp.com/v3/businesses/search", params=params)
		ratelimits = ApiKeys.select()
		if ratelimits:
			ratelimits = ApiKeys.select().get()
			ratelimits.ratelimit = r.headers['ratelimit-remaining']
		else:
			ratelimits = ApiKeys(r.headers['ratelimit-remaining'])
		ratelimits.save()

		return r.json()["businesses"]

	def get_circles(self):
		self.recursive_circles(self.main_center, self.main_radius)
		if not self.circles:
			print("No valid circles found")
			return []
		print(f"Found {len(self.circles)} circles") 
		return self.circles

	def recursive_circles(self, c, r, indent=""):
		metre_r = self.radius_lat2m((c[1],c[0]),(c[1]+r,c[0]))
		min_metre = 500
		if metre_r < min_metre:
			return
		
		if (c[0] - self.main_center[0])**2 + (c[1] - self.main_center[1])**2 >= (r+self.main_radius)**2:
			return
			
		if not(self.circle_intersecting([c,r]) or self.circle_inside([c,r])):
			return

		print(metre_r)
		if metre_r >= min_metre and metre_r <= 40000:
			search_params = {
				"term": self.search_from, 
				"limit": 50,
				"latitude": c[1],
				"longitude": c[0],
				"radius": metre_r,
				"categories": ",".join(list(map(lambda c: c, eval(self.category))))
			}
			try:
				page = self.__search(search_params)
				if len(page) <= 40:
					self.circles.append([c,metre_r,r])
					return
			except Exception as e:
				print(f"Search error: {e}")
				return
		if metre_r >= min_metre:
			x, y = self.get_hex_corners(c, r)
			for i in range(6):
				center = ((x[i] + x[i+1])/2,(y[i] + y[i+1])/2)
				self.recursive_circles(center, r/4, indent+"\t")
			self.recursive_circles(c, r/4, indent+"\t")


if __name__ == "__main__":
	x=ComputeYelpCircles('Hudson')
	x.get_circles()