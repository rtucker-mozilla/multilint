# Simplest possible comparison. Confirm left == right.
def compare_exact(left_attribute, right_attribute, left_entry, right_entry):

    try:
        left_attribute = left_attribute.encode('utf8')
    except AttributeError:
        pass
    try:
        right_attribute = right_attribute.encode('utf8')
    except AttributeError:
        pass

    return left_attribute == right_attribute


# This comparison is when the right attribute is the same as the left.
# only the right is all lowercase.
# Not likely a good real world example but a simple one to begin with for calculated comparisons.
def compare_lower_right(left_attribute, right_attribute, left_entry, right_entry):
    return left_attribute.lower() == right_attribute