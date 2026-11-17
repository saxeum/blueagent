-- Test data for local poking; applied once, tracked in schema_migrations.
INSERT INTO orders (customer, item, quantity, status) VALUES
    ('Ada Lovelace',      'widget',    2, 'pending'),
    ('Grace Hopper',      'gadget',    1, 'shipped'),
    ('Alan Turing',       'doohickey', 5, 'pending'),
    ('Katherine Johnson', 'widget',    3, 'cancelled'),
    ('Barbara Liskov',    'gizmo',     1, 'shipped');
