from app import pusher
from datetime import datetime
# New post notification
def notify_new_post(post, author):
    pusher.trigger('notifications', 'new-post', {
        'data': {
            'type': 'post',
            'message': f'{author.username} made a new post',
            'post_id': post.id,
            'author_id': author.id,
            'author_name': author.username,
            'timestamp': str(post.created_at)
        }
    })

# New comment notification
def notify_comment(comment, post):
    pusher.trigger('notifications', 'new-comment', {
        'data': {
            'type': 'comment',
            'message': f'{comment.author.username} commented on your post',
            'post_id': post.id,
            'comment_id': comment.id,
            'author_id': comment.author.id,
            'author_name': comment.author.username,
            'post_author_id': post.author.id,
            'timestamp': str(comment.created_at)
        }
    })

# Like notification
def notify_post_like(user, post):
    pusher.trigger('notifications', 'new-like', {
        'data': {
            'type': 'like',
            'message': f'{user.username} liked your post',
            'post_id': post.id,
            'liker_id': user.id,
            'liker_name': user.username,
            'post_author_id': post.author.id,
            'timestamp': str(datetime.utcnow())
        }
    })
# Like notification
def notify_comment_like(user, comment):
    pusher.trigger('notifications', 'new-like', {
        'data': {
            'type': 'like',
            'message': f'{user.username} liked your post',
            'post_id': comment.id,
            'liker_id': user.id,
            'liker_name': user.username,
            'post_author_id': comment.author.id,
            'timestamp': str(datetime.utcnow())
        }
    })
# New follower notification
def notify_follow(follower, followed):
    pusher.trigger('notifications', 'new-follow', {
        'data': {
            'type': 'follow',
            'message': f'{follower.username} started following you',
            'follower_id': follower.id,
            'follower_name': follower.username,
            'followed_id': followed.id,
            'timestamp': str(datetime.utcnow())
        }
    })

# New message notification
def notify_message(sender, recipient, message):
    pusher.trigger('notifications', 'new-message', {
        'data': {
            'type': 'message',
            'message': f'New message from {sender.username}',
            'sender_id': sender.id,
            'sender_name': sender.username,
            'recipient_id': recipient.id,
            'message_preview': message.body[:50] + '...' if len(message.body) > 50 else message.content,
            'timestamp': str(message.created_at)
        }
    })