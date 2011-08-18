from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template, Context
from tmv_app.models import *
from django.db.models import Q
import random, sys, datetime

# the following line will need to be updated to launch the browser on a web server
TEMPLATE_DIR = sys.path[0] + '/templates/'

def topic_detail(request, topic_id):    
    response = ''
    
    template_file = open(TEMPLATE_DIR + 'topic.html', 'r')
    topic_template = Template(template_file.read())
    
    topic = Topic.objects.get(id=topic_id)
    topicterms = TopicTerm.objects.filter(topic=topic_id).order_by('-score')
    doctopics = DocTopic.objects.filter(topic=topic_id).order_by('-score')[:50]
    
    terms = []
    term_bar = []
    remainder = 1
    remainder_titles = ''
    
    for tt in topicterms:
        term = Term.objects.get(pk=tt.term)
        
        terms.append(term)
        if tt.score >= .01:
            term_bar.append((True, term, tt.score * 100))
            remainder -= tt.score
        else:
            if remainder_titles == '':
                remainder_titles += term.title
            else:
                remainder_titles += ', ' + term.title
    term_bar.append((False, remainder_titles, remainder*100))
    
    topics = []
    
    docs = []
    for dt in doctopics:
        docs.append(Doc.objects.get(pk=dt.doc))
    
    nav_bar = open(TEMPLATE_DIR + 'nav_bar.html', 'r').read()
    
    topic_page_context = Context({'nav_bar': nav_bar, 'topic': topic, 'terms': terms, 'term_bar': term_bar, 'docs': docs})
    
    return HttpResponse(topic_template.render(topic_page_context))

def term_detail(request, term_id):
    response = ''
    
    template_file = open(TEMPLATE_DIR + 'term.html', 'r')
    term_template = Template(template_file.read())
    
    term = Term.objects.get(id=term_id)
    docterms = DocTerm.objects.filter(term=term_id).order_by('-score')

    docs = []
    counts = []
    proportions = []
    for dt in docterms:
        doc = Doc.objects.get(pk=dt.doc)
        docs.append(doc)
        counts.append(dt.score)
        proportions.append(100*(dt.score/doc.word_count()))
    
    nav_bar = open(TEMPLATE_DIR + 'nav_bar.html', 'r').read()
    
    term_page_context = Context({'nav_bar': nav_bar, 'term': term, 'docs': docs, 'counts': counts, 'proportions': proportions})
    
    return HttpResponse(term_template.render(term_page_context))

def doc_detail(request, doc_id):
    response = ''
    print "doc: " + str(doc_id)
    template_file = open(TEMPLATE_DIR + 'doc.html', 'r')
    doc_template = Template(template_file.read())
    
    doc = Doc.objects.get(id=doc_id)
    doctopics = DocTopic.objects.filter(doc=doc_id).order_by('-score')

    topics = []
    pie_array = []
    for dt in doctopics:
        if (dt.score >= 10):
            topic = Topic.objects.get(pk=dt.topic)
            topics.append(topic)
            pie_array.append([dt.score, '/topic/' + str(topic.id), 'topic_' + str(topic.id)])
    
    nav_bar = open(TEMPLATE_DIR + 'nav_bar.html', 'r').read()
    
    doc_page_context = Context({'nav_bar': nav_bar, 'doc': doc, 'topics': topics, 'pie_array': pie_array})
    
    return HttpResponse(doc_template.render(doc_page_context))

def topic_list_detail(request):
    response = ''
    
    template_file = open(TEMPLATE_DIR + 'topic_list.html', 'r')
    list_template = Template(template_file.read())
    
    topics = Topic.objects.all()

    terms = []
    for t in topics:
        topicterms = TopicTerm.objects.filter(topic=t.id).order_by('-score')[:5]
        temp =[]
        term_count = 5
        for tt in topicterms:
            temp.append(Term.objects.get(pk=tt.term))
            term_count -= 1
        for i in range(term_count):        
            temp.append(None)
        terms.append(temp)
    
    nav_bar = open(TEMPLATE_DIR + 'nav_bar.html', 'r').read()

    div_topics = []
    div_terms = []
    rows = []
    n = 3
    for i in xrange(0, len(topics), n):
        temp = [] 
        for j in range(5):
            K = min(len(topics), i+n)
            t = [terms[k][j] for k in range(i,K,1)]
            while len(t) < n:
                t.append(None)
            temp.append(t)
        tops = topics[i:i+n]
        while len(tops) < n:
            tops.append(None)
        rows.append((tops, temp))

    list_page_context = Context({'nav_bar': nav_bar, 'rows': rows})
    
    return HttpResponse(list_template.render(list_page_context))

def topic_presence_detail(request):
    response = ''
    
    template_file = open(TEMPLATE_DIR + 'topic_presence.html', 'r')
    presence_template = Template(template_file.read())
    
    topics = {}
    for topic in Topic.objects.all():
        score = sum([dt.score for dt in DocTopic.objects.filter(topic=topic.id)])
        topics[topic] = score
    
    sorted_topics = sorted(topics.keys(), key=lambda x: -topics[x])
    topic_tuples = []
    max_score = max(topics.values())
    for topic in sorted_topics:
        topic_tuples.append((topic, topics[topic], topics[topic]/max_score*100))
    
    nav_bar = open(TEMPLATE_DIR + 'nav_bar.html', 'r').read()

    presence_page_context = Context({'nav_bar': nav_bar, 'topic_tuples': topic_tuples})
    
    return HttpResponse(presence_template.render(presence_page_context))


def stats(request):
    template_file = open(TEMPLATE_DIR + 'stats.html', 'r')
    stats_template = Template(template_file.read())

    nav_bar = open(TEMPLATE_DIR + 'nav_bar.html', 'r').read()

    stats_page_context = Context({'nav_bar': nav_bar, 'num_docs': Doc.objects.count(), 'num_topics': Topic.objects.count(), 'num_terms': Term.objects.count(), 'start_time': RunStats.objects.get(id=1).start, 'elapsed_time': (datetime.datetime.now() - RunStats.objects.get(id=1).start), 'num_batches': RunStats.objects.get(id=1).batch_count, 'last_update': RunStats.objects.get(id=1).last_update})

    return HttpResponse(stats_template.render(stats_page_context))

def topic_random(request):
    return HttpResponseRedirect('/topic/' + str(random.randint(1, Topic.objects.count())))

def doc_random(request):
    return HttpResponseRedirect('/doc/' + str(random.randint(1, Doc.objects.count())))

def term_random(request):
    return HttpResponseRedirect('/term/' + str(random.randint(1, Term.objects.count())))
