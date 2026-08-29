#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__ == '__main__':
    with open('paths.txt', 'r') as f:
        paths = [line.strip() for line in f if line.strip()]
    
    result = ' '.join(f'"{path}"' for path in paths)
    print(result)
    
    with open('paths_result.txt', 'w') as f:
        f.write(result)
