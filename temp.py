def check_book_issue(self):
    for rec in self:
        if rec.status == 'issued':
            raise ValidationError('book already issued, it cannot be issue again')
        if rec.available_quantity == 0:
            raise ValidationError('book's quantity is zero, it cannot be issue again')