# Comments Feature for Department Head

## Overview

The Department Head can now add comments to requests. Comments are separate from final notes and approval logs, allowing for ongoing discussion and notes throughout the request review process.

## Features

✅ **Add Comments**: Department Head can add multiple comments to any request
✅ **View Comments**: All comments are displayed in the request details modal
✅ **Comment History**: Comments show author name, role, and timestamp
✅ **Real-time Updates**: Comments appear immediately after adding

## Database Model

### Comment Model
- `id`: Primary key
- `request`: Foreign key to Request
- `author`: Foreign key to User (Department Head)
- `comment`: Text field for comment content
- `created_at`: Timestamp when comment was created
- `updated_at`: Timestamp when comment was last updated

## API Endpoints

### POST `/api/head/add-comment/<request_id>/`
Add a comment to a request.

**Request Body:**
```json
{
  "comment": "Comment text here"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Comment added successfully",
  "comment": {
    "id": 1,
    "comment": "Comment text here",
    "author_name": "Department Head",
    "author_role": "head_of_dept",
    "created_at": "2026-01-09T12:41:17.713937+00:00"
  }
}
```

### GET `/api/head/request-details/<request_id>/`
Get request details including all comments.

**Response includes:**
```json
{
  "success": true,
  "request": {...},
  "approval_logs": [...],
  "comments": [
    {
      "id": 1,
      "comment": "Comment text",
      "author_name": "Department Head",
      "author_role": "head_of_dept",
      "created_at": "2026-01-09T12:41:17.713937+00:00",
      "updated_at": "2026-01-09T12:41:17.713937+00:00"
    }
  ]
}
```

## UI Features

### Request Details Modal
- **Add Comment Section**: Textarea and button to add new comments
- **Comments List**: Displays all comments in chronological order (newest first)
- **Comment Display**: Shows author name, timestamp, and comment text
- **Styling**: Clean, modern design with left border accent

### Comment Display
- Author name in bold
- Timestamp in smaller, secondary text
- Comment text with proper line breaks
- Background color to distinguish from other content

## Usage

1. **View Request Details**: Click "View Details" on any request card
2. **Add Comment**: Scroll to "Add Comment" section
3. **Enter Comment**: Type your comment in the textarea
4. **Submit**: Click "Add Comment" button
5. **View Comments**: Comments appear in the "Comments" section above

## Differences from Final Notes

| Feature | Comments | Final Notes |
|---------|----------|-------------|
| **Quantity** | Multiple comments allowed | Single final note |
| **Visibility** | Internal (Department Head view) | Visible to student |
| **Purpose** | Ongoing discussion/notes | Final decision/feedback |
| **Timing** | Can be added anytime | Typically added at end |
| **Notification** | No notification sent | Notification sent to student |

## Testing

Run the test script to verify functionality:
```bash
python test_comments.py
```

## Files Modified

1. **requests_app/models.py**: Added Comment model
2. **requests_app/views.py**: Added `add_comment` view and updated `get_request_details`
3. **requests_app/urls.py**: Added comment endpoint
4. **requests_app/admin.py**: Added Comment admin interface
5. **templates/head_dashboard.html**: Added comment UI
6. **static/css/style.css**: Added comment styling
7. **Migrations**: Created `0002_comment.py` migration

## Database Migration

To apply the changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Admin Interface

Comments can be managed in Django admin:
- View all comments
- Filter by date, author
- Search by comment text, request title, author name
