from extensions import client
from faunadb import query as q


# res = client.query(
#     q.let(
#         {
#             "x": q.get(
#                 q.match(
#                     q.index("business_by_name"),
#                     "laredo gadgets"
#                 )
#             )
#         },
#         q.if_(q.is_object(q.var("x")), q.let(
#             {'y': 'yes'}, q.var('y')
#         ), q.let({'n': 'no'}, q.var('n')))
#     )
# )



v = q.get(
    q.match(
        q.index("business_by_name"),
        "laredo gadgets"
    )
)
print(q.is_object(v))