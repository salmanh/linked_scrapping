#author https://github.com/salmanh

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import random
import time
import os
import pickle

load_dotenv()  # loads environment variables from .env file


# Set up the browser and load LinkedIn
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    driver = webdriver.Chrome(options=options)

    # Load cookies if they exist
    if os.path.exists("cookies.pkl"):
        driver.get("https://www.linkedin.com")
        with open("cookies.pkl", "rb") as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()
    else:
        driver.get("https://www.linkedin.com/login")

    return driver


# Perform login and handle 2FA
def login(driver, username, password):
    try:
        username_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        username_input.send_keys(username)
        password_input.send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        # Handle 2FA if needed
        if driver.find_elements(By.XPATH, "//input[@type='text']"):
            print("Enter 2FA code:")
            code = input()
            driver.find_element(By.XPATH, "//input[@type='text']").send_keys(code)

        # Save cookies after successful login
        pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    except NoSuchElementException as e:
        print("Login elements not found, possibly already logged in or cookies are working.")


# Visit the LinkedIn group page
def visit_group(driver, group_url):
    driver.get(group_url)


# Like, comment, repost and follow logic
def engage_with_posts(driver, comments_list, tracking_file, sleep_limits, group_url):
    time.sleep(10)
    post_selector = "//div[@data-urn][@role='region']"  # Update this as needed
    posts = driver.find_elements(By.XPATH, post_selector)
    # Load tracking file if it exists
    tracking = set()
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r') as file:
            tracking = set([line.split(",")[0] for line in file.read().splitlines()[1:]])
    old_urn_id = ""
    old_post_len = 0
    while True:
        we_are_on_the_same_page(driver, group_url)
        posts = driver.find_elements(By.XPATH, post_selector)
        if len(posts) == old_post_len:
            print("No new posts found")
            return True
        print(f"Found {len(posts)} posts")
        for post in posts:
            # time.sleep(5)
            liked, commented, reposted, followed = False, False, False, False
            try:
                # element = post.find_element(By.XPATH, '//*[@data-urn]')
                data_urn = post.get_attribute('data-urn')
                post_css_id = post.get_attribute('id')
                post_id = data_urn.split(":")[-1]
                urn_id_for_cache = data_urn
                author_ele = post.find_element(By.XPATH,".//span[contains(@class, 'update-components-actor__name')]")
                author_name = author_ele.text
                author_name = author_name.split("\n")[0] if "\n" in author_name else author_name
                ActionChains(driver).move_to_element(author_ele).perform()
                ActionChains(driver).move_to_element(post).perform()
                body = driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(Keys.PAGE_DOWN)
                # time.sleep(3)
                print(f"Processing post: {post_id}, Author: {author_name}")
                if post_id in tracking:
                    # author_name = post.find_element(By.XPATH, "//span[contains(@class, 'update-components-actor__name')]").text
                    print(f"--Skipping post {post_id} by {author_name}")
                    continue  # Skip already processed posts
                tracking.add(post_id)
                ActionChains(driver).move_to_element(post).perform()
                if urn_id_for_cache == old_urn_id:
                    print("It looks like we reached the end of the posts. Exiting...")
                    return True
                print("Processing post:", post.get_attribute('id'))


                if 1==2:
                    followed = follow_post_user(driver, post, post_css_id)
                    liked = like_post(driver, post)
                    reposted = share_repost_post(driver, post)
                    commented = comment_on_post(comments_list, driver, post)


                # Update tracking
                with open(tracking_file, 'a') as file:
                    print(f"-Writing to file: {post_id}, {liked}, {commented}, {reposted}, {followed}")
                    file.write(f"{post_id}, {liked}, {commented}, {reposted}, {followed}\n")


            except WebDriverException as e:
                print(f"Error engaging with post: {e}")
            old_urn_id = urn_id_for_cache

        # Scroll down to load more posts

        height = driver.execute_script("return document.body.scrollHeight")
        # inner_height = driver.execute_script("return window.innerHeight + window.scrollY")
        for i in range(0, height, 1000):
            body = driver.find_element(By.TAG_NAME, 'body')
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.1)
        # find show more result button and click it if it is visible:
        try:
            show_more_button = driver.find_element(By.XPATH, "//button[contains(.,'Show more results')]")
            ActionChains(driver).move_to_element(show_more_button).perform()
            time.sleep(5)
            show_more_button.click()
            print("Show more results button clicked")
        except NoSuchElementException:
            print("No show more button found")
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[contains(.,'Show more results')]")
                    )
                ).click()
                print("Show more results button clicked")
            except TimeoutException:
                posts = driver.find_elements(By.XPATH, post_selector)
                if len(posts) != old_post_len:
                    print(f"More results found, continuing new={len(posts)}, old={old_post_len}")
                    continue
            print("No show more button found")
        time.sleep(10)

        # Pause to avoid being detected as a bot
        random_sleep_time = random.randint(sleep_limits[0], sleep_limits[1])
        print(f"Sleeping for {random_sleep_time} seconds")
        time.sleep(random_sleep_time)
        old_post_len = len(posts)


def we_are_on_the_same_page(driver, group_url):
    if driver.current_url != group_url:
        visit_group(driver, group_url)


def comment_on_post(comments_list, driver, post):
    commented = False
    try:
        # Comment on the post
        print("Comment post")
        comment_button = post.find_element(By.XPATH, ".//button[contains(@aria-label, 'Comment')]")
        comment_button.click()
        comment_input = driver.switch_to.active_element
        comment_input.send_keys(random.choice(comments_list))
        time.sleep(5)
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB * 3)
        actions.perform()
        time.sleep(3)
        post_button = driver.switch_to.active_element
        post_button.click()
        time.sleep(5)

        commented = True
        print("Comment post success")
    except NoSuchElementException:
        print("Comment button not found")
    return commented


def share_repost_post(driver, post):
    reposted = False
    try:
        # Repost the post
        print("Repost post")
        try:
            repost_button = post.find_element(By.XPATH, ".//button[.//span[contains(text(), 'Share')]]")
        except NoSuchElementException:
            repost_button = post.find_element(By.XPATH, ".//button[.//span[contains(text(), 'Repost')]]")
        repost_button.click()
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB)
        time.sleep(1)
        actions.send_keys(Keys.TAB)
        actions.perform()
        repost_button = driver.switch_to.active_element
        repost_button.click()
        reposted = True
        print("Repost post success")
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE * 2)
        actions.perform()
    except NoSuchElementException:
        print("Repost button not found")
    return reposted


def like_post(driver, post):
    liked = False
    # Like the post
    try:
        print("Like post")
        like_button = post.find_element(By.XPATH, ".//button[contains(@aria-label, 'React Like')]")
        ActionChains(driver).move_to_element(like_button).perform()
        like_button.click()
        liked = True
        print("Like post success")
    except NoSuchElementException:
        print("Like button not found")  # Like button not visible, move on
    return liked


def follow_post_user(driver, post, post_css_id):
    followed = False
    # Follow user/company if visible
    try:
        print("Following user")
        follow_button = post.find_element(By.CSS_SELECTOR, f"#{post_css_id} .follow > span")
        ActionChains(driver).move_to_element(follow_button).perform()
        time.sleep(2)
        follow_button.click()
        followed = True
        print("Following user success")
    except NoSuchElementException:
        print("Follow button not found")
    return followed


# Handle disconnections
def wait_for_connection(driver):
    while True:
        try:
            driver.find_element(By.TAG_NAME, "body")
            break
        except WebDriverException:
            print("Waiting for reconnection...")
            time.sleep(10)


# Main script execution
def main():
    driver = setup_driver()

    # Perform loginpip install python-dotenv
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    login(driver, username, password)

    # Load comments
    with open('comments.txt', 'r') as file:
        comments_list = file.read().splitlines()

    # Visit the group
    group_url = "https://www.linkedin.com/groups/1976445/"
    visit_group(driver, group_url)

    # Engage with posts
    tracking_file = "tracking.txt"
    finished = False
    while not finished:
        try:
            finished = engage_with_posts(driver, comments_list, tracking_file,
                                         [5,10], group_url)
        except TimeoutException:
            print("Timed out. Reconnecting...")
            wait_for_connection(driver)

    # Close the browser
    driver.quit()


if __name__ == "__main__":
    main()
