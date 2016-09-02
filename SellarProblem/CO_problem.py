__author__ = 'sebasanper'
from openmdao.lib.datatypes.api import Array
from openmdao.main.api import Assembly, set_as_top
from openmdao.lib.drivers.api import SLSQPdriver
from openmdao.lib.optproblems import sellar


class SellarCO(Assembly):
    """Solution of the sellar analytical problem using CO.
    """

    global_des_var_targets = Array([5.0, 2.0], iotype='in')
    local_des_var_targets = Array([1.0, ], iotype='in')
    coupling_var_targets = Array([3.16, 0], iotype='in')

    def configure(self):
        # Global Optimization
        self.add('driver', SLSQPdriver())
        self.add('localopt1', SLSQPdriver())
        self.add('localopt2', SLSQPdriver())
        self.driver.workflow.add(['localopt1', 'localopt2'])

        # Local Optimization 1
        self.add('dis1', sellar.Discipline1())
        self.localopt1.workflow.add(['dis1'])

        # Local Optimization 2
        self.add('dis2', sellar.Discipline2())
        self.localopt2.workflow.add(['dis2'])

        # Parameters - Global Optimization
        self.driver.add_objective(
            '(local_des_var_targets[0])**2 + global_des_var_targets[1] + coupling_var_targets[0] + math.exp(-coupling_var_targets[1])')
        self.driver.add_parameter('global_des_var_targets[0]', low=-10.0, high=10.0)
        self.driver.add_parameter('global_des_var_targets[1]', low=0.0, high=10.0)

        self.driver.add_parameter('coupling_var_targets[0]', low=-1e99, high=1e99)
        self.driver.add_parameter('coupling_var_targets[1]', low=-1e99, high=1e99)
        self.driver.add_parameter('local_des_var_targets[0]', low=0.0, high=10.0)

        con1 = '(local_des_var_targets[0]-dis1.x1)**2+' + \
               '(global_des_var_targets[0]-dis1.z1)**2+' + \
               '(global_des_var_targets[1]-dis1.z2)**2+' + \
               '(coupling_var_targets[1]-dis1.y2)**2+' + \
               '(coupling_var_targets[0]-dis1.y1)**2<=.001'

        con2 = '(global_des_var_targets[0]-dis2.z1)**2 +' + \
               '(global_des_var_targets[1]-dis2.z2)**2 +' + \
               '(coupling_var_targets[0]-dis2.y1)**2 +' + \
               '(coupling_var_targets[1]-dis2.y2)**2 <= .001'
        self.driver.add_constraint(con1)
        self.driver.add_constraint(con2)

        self.driver.printvars = ['dis1.y1', 'dis2.y2']
        self.driver.iprint = 1

        # Parameters - Local Optimization 1

        self.localopt1.add_objective('(local_des_var_targets[0]-dis1.x1)**2+'
                                     '(global_des_var_targets[0]-dis1.z1)**2+'
                                     '(global_des_var_targets[1]-dis1.z2)**2+'
                                     '(coupling_var_targets[1]-dis1.y2)**2+'
                                     '(coupling_var_targets[0]-dis1.y1)**2')
        self.localopt1.add_parameter('dis1.x1', low=0.0, high=10.0)
        self.localopt1.add_parameter('dis1.z1', low=-10.0, high=10.0)
        self.localopt1.add_parameter('dis1.z2', low=0.0, high=10.0)
        self.localopt1.add_parameter('dis1.y2', low=-1e99, high=1e99)
        self.localopt1.add_constraint('3.16 < dis1.y1')
        self.localopt1.iprint = 1

        # Parameters - Local Optimization 2
        self.localopt2.add_objective('(global_des_var_targets[0]-dis2.z1)**2 + ' +
                                     '(global_des_var_targets[1]-dis2.z2)**2 + ' +
                                     '(coupling_var_targets[0]-dis2.y1)**2 + ' +
                                     '(coupling_var_targets[1]-dis2.y2)**2')
        self.localopt2.add_parameter('dis2.z1', low=-10.0, high=10.0)
        self.localopt2.add_parameter('dis2.z2', low=0.0, high=10.0)
        self.localopt2.add_parameter('dis2.y1', low=-1e99, high=1e99)
        self.localopt2.add_constraint('dis2.y2 < 24.0')
        self.localopt2.iprint = 1

if __name__ == "__main__":

    import time

    prob = SellarCO()

    prob.dis1.z1 = 5.0
    prob.dis2.z1 = 5.0

    prob.dis1.z2 = 2.0
    prob.dis2.z2 = 2.0

    prob.dis1.x1 = 1.0

    prob.dis1.y2 = 1.0
    prob.dis2.y1 = 1.0

    prob.global_des_var_targets = [5.0, 2.0]
    prob.local_des_var_targets = [1.0, ]
    prob.coupling_var_targets = [1.0, 1.0]

    tt = time.time()

    prob.run()

    # prob.driver.workflow.check_gradient()

    print "\n"
    print "Minimum found at (%f, %f, %f)" % (prob.dis1.z1,
                                             prob.dis1.z2,
                                             prob.dis1.x1)
    print "Minimum target was at (%f, %f, %f)" % (prob.global_des_var_targets[0],
                                             prob.global_des_var_targets[1],
                                             prob.local_des_var_targets[0])
    print "Coupling vars: %f, %f" % (prob.dis1.y1, prob.dis2.y2)
    print "Coupling var targets: %f, %f" % (prob.coupling_var_targets[0], prob.coupling_var_targets[1])
    print "Minimum objective: ", prob.driver.eval_objective()
    print "Elapsed time: ", time.time()-tt, "seconds"