#!/usr/bin/python

# onlinewikipedia.py: Demonstrates the use of online VB for LDA to
# analyze a bunch of random Wikipedia articles.
#
# Copyright (C) 2010  Matthew D. Hoffman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cPickle, string, numpy, getopt, sys, random, time, re, pprint, gc

import onlineldavb
import wikirandom

# import file for easy access to browser database
sys.path.append('<ABSOLUTE PATH TO SRC DIR>/BasicBrowser/')
import db

def main():
    """
    Downloads and analyzes a bunch of random Wikipedia articles using
    online VB for LDA.
    """

    # The number of documents to analyze each iteration
    batchsize = 64
    # The total number of documents in Wikipedia
    D = 3.3e6
    # The number of topics
    K = 100

    # How many documents to look at
    if (len(sys.argv) < 3):
        documentstoanalyze = int(D/batchsize)
    else:
        documentstoanalyze = int(sys.argv[2])
    
    #read old lambda file
    left_off = int(sys.argv[1])
    old_lambda = numpy.loadtxt('lambda-%d.dat' % left_off)

    # Our vocabulary
    vocab = file('./dictnostops.txt').readlines()
    W = len(vocab)
    
    # Initialize the algorithm with alpha=1/K, eta=1/K, tau_0=1024, kappa=0.7
    olda = onlineldavb.OnlineLDA(vocab, K, D, 1./K, 1./K, 1024., 0.7, old_lambda)
    # Run until we've seen D documents. (Feel free to interrupt *much*
    # sooner than this.)
    for iteration in range(left_off, left_off + documentstoanalyze):
        # Download some articles
        (docset, articlenames) = \
            wikirandom.get_random_wikipedia_articles(batchsize)
        
        # Give them to online LDA
        (gamma, bound) = olda.update_lambda(docset)
        
        # Compute an estimate of held-out perplexity
        (wordids, wordcts) = onlineldavb.parse_doc_list(docset, olda._vocab)
        
        # Arrays for adding batches of data to the DB
        doc_array = []
        doc_term_array = []
        
        for d in range(len(articlenames)):
            doc_array.append((articlenames[d], docset[d]))
        
        # Add a batch of docs to the DB; this is the one DB task that is not in
        # the separate DB write thread since later tasks depend on having doc ids.
        # Since writes take so long, this also balaces the two threads time-wise.
        doc_ids = db.add_docs(doc_array)
	
        for d in range(len(articlenames)):        
            for term in range(len(wordids[d])):
                doc_term_array.append((doc_ids[d], wordids[d][term], wordcts[d][term]))
        
        db.add_doc_terms(doc_term_array)
        
        doc_topic_array = []
        for d in range(len(gamma)):
            doc_size = len(docset[d])
            for k in range(len(gamma[d])):
                doc_topic_array.append((doc_ids[d], k, gamma[d][k], gamma[d][k]/doc_size))
        db.add_doc_topics(doc_topic_array)

        perwordbound = bound * len(docset) / (D * sum(map(sum, wordcts)))
        print '%d:  rho_t = %f,  held-out perplexity estimate = %f' % \
            (iteration, olda._rhot, numpy.exp(-perwordbound))

        # Save lambda, the parameters to the variational distributions
        # over topics, and gamma, the parameters to the variational
        # distributions over topic weights for the articles analyzed in
        # the last iteration.
        if (iteration % 10 == 0):
            numpy.savetxt('lambda-%d.dat' % iteration, olda._lambda)
            numpy.savetxt('gamma-%d.dat' % iteration, gamma)
            
            topic_terms_array =[]
            for topic in range(len(olda._lambda)):
                lambda_sum = sum(olda._lambda[topic])
                
                for term in range(len(olda._lambda[topic])):
                    topic_terms_array.append((topic, term, olda._lambda[topic][term]/lambda_sum))
            db.update_topic_terms(K, topic_terms_array)
                
            db.update_topic_titles()
            gc.collect() # probably not necesary, but precautionary for long runs
            db.print_task_update()
        db.increment_batch_count()
    
    # The DB thread ends only when it has both run out of tasks and it has been
    # signaled that it will not be recieving any more tasks
    db.signal_end()

if __name__ == '__main__':
    main()