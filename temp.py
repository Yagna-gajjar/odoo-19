@api.model_create_multi
def create(self, val_list):
    prd = super().create(val_list)
    for vals in val_list:
        if not vals.get('isbn_code'):
            vals['isbn_code'] = 'NOT-ASSIGNED'
    return prd