import random



def random_delay(min, max):
    # min = minimum number of seconds
    # max = maximum number of seconds
    delay = random.uniform(min, max)
    #await page.wait_for_timeout(delay * 1000)
    return delay


def random_mouse_movement():
    x = random.randint(100, 700)
    y = random.randint(100, 700)
    #await page.mouse.move(x, y)
    #await page.wait_for_timeout(random.randint(300, 800))
    return x, y


def exp_wait_time(attempt):
    return (2 ** attempt) * 10