import blogeteer


def test_slugify():
    input_result = {
        'banana man': 'banana-man',
        'a%%%%b': 'a-b',
        'a--b': 'a-b',
        'hey--hey----hey$*(#%&@#': 'hey-hey-hey'
    }
    for (key, value) in input_result.items():
        assert blogeteer.slugify(key) == value


# ------------------------------------------------------------------------------------------------

# MAIN

def run_tests():
    test_slugify()


if __name__ == '__main__':
    run_tests()
