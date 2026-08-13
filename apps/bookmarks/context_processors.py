# from .models import Bookmark


# def user_bookmarks(request):
#     """Makes bookmarked IDs available in all templates."""
#     if request.user.is_authenticated:
#         bookmarked_property_ids = list(
#             Bookmark.objects.filter(
#                 user=request.user, room=None
#             ).values_list('property_id', flat=True)
#         )
#         bookmarked_room_ids = list(
#             Bookmark.objects.filter(
#                 user=request.user, property=None
#             ).values_list('room_id', flat=True)
#         )
#         bookmarks_count = Bookmark.objects.filter(user=request.user).count()
#         compare_ids     = request.session.get('compare_ids', [])
#         return {
#             'bookmarked_property_ids': bookmarked_property_ids,
#             'bookmarked_room_ids':     bookmarked_room_ids,
#             'bookmarks_count':         bookmarks_count,
#             'compare_count':           len(compare_ids),
#         }
#     return {
#         'bookmarked_property_ids': [],
#         'bookmarked_room_ids':     [],
#         'bookmarks_count':         0,
#         'compare_count':           0,
#     }

from .models import Bookmark


def user_bookmarks(request):
    """Makes bookmarked IDs available in all templates."""

    user = getattr(request, "user", None)

    if user is not None and user.is_authenticated:
        bookmarked_property_ids = list(
            Bookmark.objects.filter(user=user, room=None).values_list(
                "property_id", flat=True
            )
        )

        bookmarked_room_ids = list(
            Bookmark.objects.filter(user=user, property=None).values_list(
                "room_id", flat=True
            )
        )

        bookmarks_count = Bookmark.objects.filter(user=user).count()

        compare_ids = request.session.get("compare_ids", [])

        return {
            "bookmarked_property_ids": bookmarked_property_ids,
            "bookmarked_room_ids": bookmarked_room_ids,
            "bookmarks_count": bookmarks_count,
            "compare_count": len(compare_ids),
        }

    return {
        "bookmarked_property_ids": [],
        "bookmarked_room_ids": [],
        "bookmarks_count": 0,
        "compare_count": 0,
    }
