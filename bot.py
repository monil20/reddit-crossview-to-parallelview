import praw
import requests
import os
import cv2
import numpy as np

from praw.models import Comment
from imgurpython import ImgurClient

DIR = os.path.join(os.getcwd(), "posts")


class Utils:
    def download_image(self, url):
        if url.endswith((".jpg", ".jpeg", ".png", ".gif")):
            img = requests.get(url).content
            filename = os.path.basename(url)
            fq_filename = os.path.join(DIR, filename)
            with open(fq_filename, "wb") as f:
                f.write(img)
            return fq_filename

    def flip_image_halves(self, fq_filename):
        image = cv2.imread(fq_filename)
        flipped_img = np.roll(image, image.shape[1] // 2, axis=1)
        cv2.imwrite(fq_filename, flipped_img)

    def upload_to_imgur(self, fq_filename):
        env_variables = os.environ.items()
        try:
            client = ImgurClient(
                env_variables["IMGUR_CLIENT_ID"],
                env_variables["IMGUR_CLIENT_SECRET"],
            )
        except Exception:
            return None
        return client.upload_from_path(fq_filename).get("link")


class ConvertToParallel:
    def __init__(self, conf):
        self.reddit = praw.Reddit(conf)

    def get_pending_replies(self):
        mentions_list = list(self.reddit.inbox.mentions(limit=None))
        unread_messages = []
        for item in self.reddit.inbox.unread(limit=None):
            if isinstance(item, Comment):
                unread_messages.append(item)

        return set(mentions_list).intersection(unread_messages)

    def convert_and_reply(self):
        utils = Utils()
        processed_images = []
        for comment in self.get_pending_replies():
            filename = utils.download_image(comment.submission.url)
            if not filename:
                continue
            utils.flip_image_halves(filename)
            hosted_link = utils.upload_to_imgur(filename)
            if not hosted_link:
                continue
            comment.reply(
                f"Hey, I am a ParallelView bot developed by u/monilandharia. Your image has been converted and hosted at [imgur]({hosted_link}). You can trigger me by mentioning my name in a post's comment. Help me advance by contributing at [github](https://github.com/monil20/reddit-crossview-to-parallelview)."
            )
            processed_images.append(comment)
            os.remove(filename)

        if processed_images:
            self.reddit.inbox.mark_read(processed_images)


if __name__ == "__main__":
    if not os.path.exists(DIR):
        os.makedirs(DIR)
    bot = ConvertToParallel("parallelview-bot")
    bot.convert_and_reply()