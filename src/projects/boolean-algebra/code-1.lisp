(defun notation (exp &optional vars)
  (let (variables)
    (labels ((infix-binding-power (op)
               (case op
                 (or (values 1 2))
                 ((and xor) (values 3 4))
                 (|)| (values nil nil '|)|))
                 (t (values 3 4 'implicit-*))))
             (postfix-binding-power (op)
               (case op
                 (not 10)
                 (t nil)))
             (infix->prefix (min-bp)
               (loop with lhs = (let ((lhs (pop exp)))
                                  (case lhs
                                    (|(| (prog1 (infix->prefix 0)
                                           (unless (eq (pop exp) '|)|)
                                             (error "No closing parenthesis somewhere lol"))))
                                    ((or and xor) (list lhs (infix->prefix lhs)))
                                    (t lhs)))
                     for op = (car exp)
                     do (unless op (loop-finish))
                        (block thing
                          (multiple-value-bind (lhs-bp) (postfix-binding-power op)
                            (when lhs-bp
                              (when (< lhs-bp min-bp)
                                (loop-finish))
                              (pop exp)
                              (setf lhs (list op lhs))
                              (return-from thing)))
                          (multiple-value-bind (lhs-bp rhs-bp special) (infix-binding-power op)
                            (cond ((or (eq special '|)|) (< lhs-bp min-bp))
                                   (loop-finish))
                                  ((eq special 'implicit-*)
                                   (setf op 'and))
                                  (t
                                   (pop exp)))
                            (setf lhs (list op lhs (infix->prefix rhs-bp)))))
                     finally (return lhs)))
             (lex (exp)
               (loop for x across exp
                     append (if (alpha-char-p x)
                                (let ((a (read-from-string (string x))))
                                  (pushnew a variables)
                                  (list a))
                                (case x
                                  ((#\') '(not))
                                  ((#\+) '(or))
                                  ((#\*) '(and))
                                  ((#\^) '(xor))
                                  ((#\() '(|(|))
                                  ((#\)) '(|)|))
                                  ((#\0) '(nil))
                                  ((#\1) '(t))
                                  ((#\space))
                                  (t (error "wot in tarnation is '~a' doing here" x)))))))
      (setf exp (lex exp))
      (list (mapcar (lambda (x) (read-from-string (string x)))
                    (sort (union vars variables) #'var<=))
                                                   (infix->prefix 0)))))
