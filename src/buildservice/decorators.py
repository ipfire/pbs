#!/usr/bin/python

class lazy_property(property):
	"""
		The property is only computed once and then being
		cached until the end of the lifetime of the object.
	"""
	def __init__(self, fget, fset=None, fdel=None, doc=None):
		property.__init__(self, fget=fget, fset=fset, fdel=fdel, doc=doc)

		# Make a cache key
		self._name = "_cache_%s" % self.fget.__name__

	def __get__(self, instance, owner):
		if instance is None:
			return self

		if hasattr(instance, self._name):
			result = getattr(instance, self._name)
		else:
			if not self.fget is None:
				result = self.fget(instance)

			setattr(instance, self._name, result)

		return result

	def __set__(self, instance, value):
		if instance is None:
			raise AttributeError

		if self.fset is None:
			setattr(instance, self._name, value)
		else:
			self.fset(instance, value)

			# Remove any cached attributes
			try:
				delattr(instance, self._name)
			except AttributeError:
				pass
