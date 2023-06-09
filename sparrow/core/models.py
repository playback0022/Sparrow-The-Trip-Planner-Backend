from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

defaultProfilePhoto = 'default-profile-photo.jpeg'


# many-to-many between Route & Attraction
class isWithin (models.Model):
    route = models.ForeignKey('Route', on_delete=models.CASCADE, db_column='route_id')
    attraction = models.ForeignKey('Attraction', on_delete=models.CASCADE, db_column='attraction_id')
    # the orderNumber of the attraction in the current route
    orderNumber = models.IntegerField(db_column='order_number') 
    
    class Meta:
        db_table = 'isWithin'
        unique_together = ('route', 'attraction')
        default_related_name = 'isWithin'

    def __str__(self):
        return f'Attraction "{self.attraction}" in route "{self.route}"'


class Route(models.Model):
    title = models.CharField(max_length=50, db_column='title')
    description = models.CharField(max_length=3000, db_column='description')
    verified = models.BooleanField(db_column='verified', default=False)
    public = models.BooleanField(db_column='public')
    startingPointLat = models.FloatField(db_column='starting_point_lat')
    startingPointLon = models.FloatField(db_column='starting_point_lon')
    publicationDate = models.DateTimeField(auto_now_add=True, db_column='routePublicationDate')
    user = models.ForeignKey('Member', on_delete=models.CASCADE, null=True, blank=True, db_column='user_id')  # nullable
    group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, db_column='group_id')  # nullable

    class Meta:
        db_table = 'route'
        ordering = ['-publicationDate']
        default_related_name = 'route'

    def clean(self):
        if (self.group is None and self.user is None) or (self.group is not None and self.user is not None):
            raise ValidationError("Either a group or a member must be specified!")

    def __str__(self):
        return self.title


class Attraction(models.Model):
    name = models.CharField(max_length=100, db_column='name')
    generalDescription = models.CharField(max_length=3000, db_column='general_description')
    latitude = models.FloatField(db_column='latitude')
    longitude = models.FloatField(db_column='longitude')

    class Meta:
        db_table = 'attraction'
        ordering = ['name']
        default_related_name = 'attraction'

    def __str__(self):
        return self.name


# member model, extending the User model via a one-to-one relationship;
class Member(models.Model):
    baseUser = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    profilePhoto = models.ImageField(upload_to='profile-photos', db_column='profile_photo', default=defaultProfilePhoto)
    birthDate = models.DateField(null=True, db_column='birth_date')

    class Meta:
        db_table = 'member'
        ordering = ['baseUser']
        default_related_name = 'user'

    def __str__(self):
        return self.baseUser.username


class Group(models.Model):
    name = models.CharField(max_length=30, db_column='name')
    description = models.CharField(max_length=1500, db_column='description')
    
    class Meta:
        db_table = 'group'
        default_related_name = 'group'

    def __str__(self):
        return self.name


# associative table between 'Member' and 'Group'
class BelongsTo(models.Model):
    user = models.ForeignKey('Member', on_delete=models.CASCADE, db_column='user_id')
    group = models.ForeignKey('Group', on_delete=models.CASCADE, db_column="group_id")
    isAdmin = models.BooleanField(db_column="isAdmin")
    nickname = models.CharField(max_length=50, null=True, blank=True, db_column="nickname")

    class Meta:
        db_table = 'belongsTo'
        default_related_name = 'belongsTo'
        # cannot have multiple identical entries for belonging relationship
        unique_together = ('user', 'group')

    def __str__(self):
        return f'User "{self.user}" is in group "{self.group}" as "{self.nickname}"'


# status model, used to store information about the state of a journey, 
# such as whether it is completed, finished, ongoing, etc.
class Status(models.Model):
    status = models.CharField(max_length=50, db_column='status')
    
    class Meta:
        db_table = 'status'
        default_related_name = 'status'

    def __str__(self):
        return self.status
    

# notebook model, used to store information about a user's experience with a particular route
# this information includes their impressions, notes, and any photos they took during the trip
# additionally, the model records the date and time of the journey;
class Notebook(models.Model):
    route = models.ForeignKey('Route', on_delete=models.CASCADE, db_column='route_id')
    user = models.ForeignKey('Member', on_delete=models.CASCADE, db_column='user_id')
    status = models.ForeignKey('Status', on_delete=models.CASCADE, db_column='status_id')

    title = models.CharField(max_length = 50, db_column='title')
    note = models.CharField(max_length = 3000, db_column = 'note')
    dateStarted = models.DateField(auto_now_add=True, db_column = 'date_started')
    dateCompleted = models.DateField(null = True, db_column = 'date_completed') # nullable
    
    class Meta:
        db_table = 'notebook'
        # descending order for dateStarted, dateCompleted, in order to show the most recent trips first
        ordering = ['-dateStarted', '-dateCompleted', 'title']
        default_related_name = 'notebook'

    def __str__(self):
        return f'"{self.title}" by {self.user.username}'

        
class Tag(models.Model):
    tagName = models.CharField(max_length=50, db_column='tag_name')

    class Meta:
        db_table = 'tag'
        ordering = ['tagName']
        default_related_name = 'tag'

    def __str__(self):
        return self.tagName


class RatingFlagType(models.Model):
    type = models.CharField(max_length=50, db_column='type')
    
    class Meta:
        db_table = 'ratingFlagType'
        default_related_name = 'ratingFlagType'

    def __str__(self):
        return self.type


# many - many between Tag & Attraction
class IsTagged(models.Model):
    attraction = models.ForeignKey('Attraction', on_delete=models.CASCADE, db_column='attraction_id')
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE, db_column='tag_id')

    class Meta:
        db_table = 'isTagged'
        unique_together = ('attraction', 'tag')
        default_related_name = 'isTagged'
        # orders the isTagged objects by the id of the Attraction, in reverse order of the id of the isTagged model itself
        # so that the most recent tag for each Attraction appears first.
        ordering = ['attraction', '-id']

    def __str__(self):
        return f'"{self.attraction.name}" tagged as "{self.tag.tagName}"'
  

# a rating can be associated with either a route or an attraction    
class RatingFlag(models.Model):
    user = models.ForeignKey('Member', on_delete=models.CASCADE, db_column='user_id')
    rating = models.ForeignKey('RatingFlagType', on_delete=models.CASCADE, db_column='rating_flag_type_id')
    comment = models.CharField(max_length=1000, null = True, blank = True, db_column='comment')
    route = models.ForeignKey('Route', null=True, blank=True, on_delete=models.CASCADE, db_column='route_id') # nullable
    attraction = models.ForeignKey('Attraction', null=True, blank=True, on_delete=models.CASCADE, db_column='attraction_id') # nullable
    
    class Meta:
        db_table = 'ratingFlag'
        default_related_name = 'ratingFlag'

    def __str__(self):
        return f'"{self.user.baseUser.username}" rated resource as "{self.rating.type}": "{self.comment}..."'


class Image(models.Model):
    imagePath = models.CharField(max_length=300, null = False, blank = False, db_column = 'imagePath', db_index=True)
    notebook = models.ForeignKey('Notebook', on_delete=models.CASCADE, null=True, blank=True, db_column='notebook_id') # nullable
    attraction = models.ForeignKey('Attraction', on_delete=models.CASCADE, null=True, blank=True, db_column='attraction_id') # nullable
    # setting up a timestamp is useful for letting users know when an image was taken 
    # and for indicating if the information may be outdated or no longer available
    timestamp = models.DateTimeField(auto_now_add=True, null = False, db_column = 'datePosted')
    owner = models.ForeignKey('Member', null=True, on_delete=models.CASCADE, db_column='owner_id')

    class Meta:
        db_table = 'Image'
        default_related_name = 'image'

    def __str__(self):
        return self.imagePath
