from aworld.replay_buffer.query_filter import QueryBuilder
from aworld.logs.util import logger


def example():
    '''
    expression: task_id = "123"
    return :
        {
            'field': 'task_id',
            'value': '123',
            'op': 'eq'
        }
    '''
    qb = QueryBuilder()
    query = qb.eq("task_id", "123").build()
    logger.info(query)


def example1():
    '''
    expression: (task_id = "123" and agent_id = "111") or (task_id = "456" and agent_id = "222")
    return : 
        {
            'or_': [{
                'and_': [{
                    'field': 'task_id',
                    'value': '123',
                    'op': 'eq'
                }, {
                    'field': 'agent_id',
                    'value': '111',
                    'op': 'eq'
                }]
            }, {
                'and_': [{
                    'field': 'task_id',
                    'value': '456',
                    'op': 'eq'
                }, {
                    'field': 'agent_id',
                    'value': '222',
                    'op': 'eq'
                }]
            }]
        }
    '''
    qb = QueryBuilder()
    query = (qb.eq("task_id", "123")
             .and_()
             .eq("agent_id", "111")
             .or_()
             .nested(QueryBuilder()
                     .eq("task_id", "456")
                     .and_()
                     .eq("agent_id", "222"))
             .build())
    logger.info(query)


def example2():
    '''
    expression: task_id = "123" and (agent_id = "111" or agent_id = "222")
    return :
        {
            'and_': [{
                'field': 'task_id',
                'value': '123',
                'op': 'eq'
            }, {
                'or_': [{
                    'field': 'agent_id',
                    'value': '111',
                    'op': 'eq'
                }, {
                    'field': 'agent_id',
                    'value': '222',
                    'op': 'eq'
                }
            }
        }   
    '''
    qb = QueryBuilder()
    query = (qb.eq("task_id", "123")
             .and_()
             .nested(QueryBuilder()
                     .eq("agent_id", "111")
                     .or_()
                     .eq("agent_id", "222"))
             .build())
    logger.info(query)

if __name__ == "__main__":
    example()
    example1()
    example2()
