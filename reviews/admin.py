from django.contrib import admin
from .models import Review, HostReview


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['author', 'room', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['author__username', 'room__name']


@admin.register(HostReview)
class HostReviewAdmin(admin.ModelAdmin):
    list_display = ['author', 'target_user', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['author__username', 'target_user__username']