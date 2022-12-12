import time


def simple_wait(seconds_to_wait=3):
    """
    Simple function to wait N amount of seconds.
    """
    print("Waiting for {} seconds...".format(seconds_to_wait))
    time.sleep(seconds_to_wait)


## ONLY FOR LOCAL TESTS! (OWN COMPUTER VALIDATIONS)
if __name__ == "__main__":
    print("Start.")
    print("waiting 5 .....")
    simple_wait(5)
    print("waiting 10 ..........")
    simple_wait(5)
    print("waiting 2 .....")
    simple_wait(2)
    print("End.")
