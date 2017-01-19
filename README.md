# Junos Templatize
Utility to convert Junos configuration into a jinja2 template 
based on a YAML config file

The variable path definitions use standard regex matching to 
find the appropriate string to replace with a jinja2 variable syntax

# Example

## example config
```
cat jt.config | grep -v '^#'
---

template_name: mx_config.j2
template_vars: mx_config.yml

template_stanzas:
  - interfaces
  - system
  - protocols

debug: false


variablize:
  - path:
      - interfaces
      - '(?:ge|xe|et)-\d+\/\d+\/\d+'
    name: interface

  - path:
      - interfaces
      - '(?:lo0|(?:ge|xe|et)-\d+\/\d+\/\d+)'
      - 'unit \d+'
      - 'family inet'
      - address
    name: ip_address

  - path:
      - system
      - hostname
    name: hostname
```

## Running the utility
```
junos_templatize.py -c jt.config -f mx_lab.config
template written to mx_config.j2
template vars written to mx_config.yml
```

## Examine the resulting template and variable file

```
cat mx_config.j2
interfaces {
    {{ interface_0 }} {
        unit 0 {
            family inet {
                unnumbered-address lo0.0;
            }
            family mpls;
        }
    }
    {{ interface_1 }} {
        flexible-vlan-tagging;
        mtu 1522;
        encapsulation flexible-ethernet-services;
    }
    {{ interface_2 }} {
        unit 0 {
            family inet {
                unnumbered-address lo0.0;
            }
            family mpls;
        }
    }
    {{ interface_3 }} {
        mtu 1522;
        encapsulation ethernet-ccc;
        unit 0 {
            description "No description available for selected UNI interface.";
            family ccc {
                filter {
                    input filter_in_{{ interface_3 }};
                }
            }
        }
    }
    {{ interface_4 }} {
        mtu 1522;
        encapsulation ethernet-ccc;
    }
    {{ interface_5 }} {
        description "MGMT NET 10.1.254.0/25";
        unit 0 {
            family inet {
                address {{ ip_address_0 }};
            }
        }
    }
    {{ interface_6 }} {
        mtu 2000;
        encapsulation ethernet-ccc;
    }
    lo0 {
        unit 0 {
            family inet {
                address {{ ip_address_1 }};
            }
        }
    }
}
protocols {
    rsvp {
        traceoptions {
            file rsvp.log;
            flag state;
            flag error;
        }
        interface {{ interface_2 }}.0;
        interface lo0.0;
        interface {{ interface_0 }}.0;
    }
    mpls {
        log-updown {
            trap;
            trap-path-down;
            trap-path-up;
        }
        traceoptions {
            file mpls.log size 3m files 2;
            flag error;
        }
        expand-loose-hop;
        no-cspf;
        label-switched-path 048030_e_to_10_1_48_30 {
            from 10.1.48.1;
            to 10.1.48.30;
            ldp-tunneling;
            fast-reroute;
            primary w_via_048010 {
                class-of-service 1;
                hop-limit 255;
            }
            secondary p_via_048040 {
                class-of-service 1;
                hop-limit 255;
                standby;
            }
        }
        path w_via_048010 {
            10.1.48.10 loose;
        }
        path p_via_048030 {
            10.1.48.30 loose;
        }
        path p_via_048040 {
            10.1.48.40 loose;
        }
        interface {{ interface_2 }}.0;
        interface lo0.0;
        interface {{ interface_0 }}.0;
    }
    ospf {
        traffic-engineering;
        export [ static direct ];
        area 0.0.0.3 {
            interface {{ interface_2 }}.0 {
                interface-type p2p;
            }
            interface {{ interface_0 }}.0 {
                interface-type p2p;
            }
        }
        area 0.0.0.0 {
            interface lo0.0 {
                passive;
            }
        }
    }
    ldp {
        interface {{ interface_0 }}.0;
        interface {{ interface_2 }}.0;
        interface lo0.0;
    }
    l2circuit {
        neighbor 10.1.48.30 {
            interface {{ interface_3 }}.0 {
                virtual-circuit-id 2;
                no-control-word;
                community 048030_e_to_10_1_48_30;
                mtu 1522;
            }
        }
        neighbor 10.1.48.10;
    }
    oam {
        ethernet {
            connectivity-fault-management {
                performance-monitoring {
                    sla-iterator-profiles {
                        StdDef-Loss {
                            measurement-type loss;
                            cycle-time 1000;
                            iteration-period 2000;
                        }
                        StdDef-SFL {
                            measurement-type statistical-frame-loss;
                            cycle-time 10;
                            iteration-period 2000;
                        }
                    }
                }
                maintenance-domain Default-Domain {
                    level 1;
                    maintenance-association PW_2 {
                        continuity-check {
                            interval 10ms;
                            loss-threshold 3;
                            hold-interval 10;
                        }
                        mep 2 {
                            interface {{ interface_3 }}.0;
                            direction up;
                            priority 0;
                            auto-discovery;
                            lowest-priority-defect all-defects;
                        }
                    }
                    maintenance-association test_cfm_2 {
                        continuity-check {
                            interval 10ms;
                            loss-threshold 3;
                            hold-interval 10;
                        }
                        mep 1 {
                            interface {{ interface_2 }}.0;
                            direction down;
                            priority 0;
                            auto-discovery;
                            lowest-priority-defect all-defects;
                        }
                    }
                }
            }
        }
    }
    lldp {
        interface all;
    }
}
```

```
cat mx_config.yml 
---

interface_0: xe-0/0/0
interface_1: ge-1/0/9
interface_2: ge-1/1/0
interface_3: ge-1/1/1
interface_4: ge-1/1/2
interface_5: ge-1/1/5
interface_6: ge-1/1/9
ip_address_0: 10.1.254.61/25
ip_address_1: 10.1.48.1/25

```