from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Bookmark
from apps.properties.models import Property, Room


@login_required
def toggle_property_bookmark(request, pk):
    """Toggle bookmark for a whole property."""
    property = get_object_or_404(Property, pk=pk)
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user, property=property, room=None
    )
    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"bookmarked": bookmarked})

    messages.success(
        request, "Added to favorites!" if bookmarked else "Removed from favorites."
    )
    return redirect(request.META.get("HTTP_REFERER", "bookmarks:list"))


@login_required
def toggle_room_bookmark(request, property_pk, room_pk):
    """Toggle bookmark for an individual room."""
    room = get_object_or_404(Room, pk=room_pk, property__pk=property_pk)
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user, room=room, property=None
    )
    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"bookmarked": bookmarked})

    messages.success(
        request, "Added to favorites!" if bookmarked else "Removed from favorites."
    )
    return redirect(request.META.get("HTTP_REFERER", "bookmarks:list"))


@login_required
def bookmark_list(request):
    """Show all bookmarks with compare option."""
    bookmarks = Bookmark.objects.filter(user=request.user).select_related(
        "property", "room", "room__property"
    )

    # Get compare list from session
    compare_ids = request.session.get("compare_ids", [])

    return render(
        request,
        "bookmarks/bookmark_list.html",
        {
            "bookmarks": bookmarks,
            "compare_ids": compare_ids,
        },
    )


@login_required
def remove_bookmark(request, pk):
    """Remove a bookmark."""
    bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)
    if request.method == "POST":
        bookmark.delete()
        messages.success(request, "Removed from favorites.")
    return redirect("bookmarks:list")


@login_required
def toggle_compare(request, pk):
    """Add/remove bookmark from compare list (max 3)."""
    bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)
    compare_ids = request.session.get("compare_ids", [])

    if pk in compare_ids:
        compare_ids.remove(pk)
        action = "removed"
    else:
        if len(compare_ids) >= 3:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "error": "max",
                        "message": "You can compare up to 3 properties at a time.",
                    }
                )
            messages.error(request, "You can compare up to 3 properties at a time.")
            return redirect("bookmarks:list")
        compare_ids.append(pk)
        action = "added"

    request.session["compare_ids"] = compare_ids
    request.session.modified = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"action": action, "count": len(compare_ids)})

    return redirect("bookmarks:list")


@login_required
def compare_view(request):
    """Compare up to 3 bookmarked properties side by side."""
    compare_ids = request.session.get("compare_ids", [])

    if len(compare_ids) < 2:
        messages.error(request, "Please select at least 2 properties to compare.")
        return redirect("bookmarks:list")

    bookmarks = Bookmark.objects.filter(
        pk__in=compare_ids, user=request.user
    ).select_related("property", "room", "room__property")

    return render(
        request,
        "bookmarks/compare.html",
        {
            "bookmarks": bookmarks,
            "compare_ids": compare_ids,
        },
    )


@login_required
def clear_compare(request):
    """Clear compare list."""
    request.session["compare_ids"] = []
    request.session.modified = True
    return redirect("bookmarks:list")
